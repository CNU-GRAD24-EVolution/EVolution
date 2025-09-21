import time
import boto3
import json
import os
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError
from botocore.config import Config

def get_secret(key):
    """
    환경변수에서 비밀 키 가져오기
    """
    return os.environ.get(key)

def lambda_handler(event, context):
    """
    간헐적 ConnectTimeoutError 해결을 위한 개선된 Lambda 함수
    """
    
    # 설정
    access_key = get_secret('AWS_ACCESS_KEY_ID')
    secret_key = get_secret('AWS_SECRET_ACCESS_KEY')
    region = get_secret('AWS_REGION')
    instance_id = get_secret('EC2_INSTANCE_ID')
    
    # 연결 설정 최적화 (타임아웃 증가 + 재시도)
    config = Config(
        region_name=region,
        retries={
            'max_attempts': 5,  # 재시도 횟수 증가
            'mode': 'adaptive'  # 적응형 재시도
        },
        connect_timeout=60,  # 연결 타임아웃 증가
        read_timeout=120,    # 읽기 타임아웃 증가
        max_pool_connections=10
    )
    
    try:
        print("🚀 Lambda 함수 시작")
        print(f"⏰ 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # AWS 클라이언트 생성 (재시도 로직 포함)
        ec2_client = create_client_with_retry("ec2", access_key, secret_key, config)
        ssm_client = create_client_with_retry("ssm", access_key, secret_key, config)
        
        if not ec2_client or not ssm_client:
            return create_error_response("AWS 클라이언트 생성 실패")
        
        print("✅ AWS 클라이언트 생성 완료")
        
        # 1. 인스턴스 시작 (재시도 포함)
        if not start_instance_with_retry(instance_id, ec2_client):
            return create_error_response("인스턴스 시작 실패")
        
        # 2. 인스턴스 상태 확인 (재시도 포함)
        if not wait_for_instance_ready(instance_id, ec2_client, ssm_client):
            return create_error_response("인스턴스 준비 대기 실패")
        
        # 3. 노트북 실행 (재시도 포함)
        command_id = execute_notebook_with_retry(instance_id, ssm_client)
        if not command_id:
            return create_error_response("노트북 실행 실패")
        
        # 4. 실행 완료 대기
        success = wait_for_completion_with_retry(command_id, instance_id, ssm_client)
        
        # 5. 인스턴스 중지는 주석 처리 (비용 절약을 위해 필요시 활성화)
        # stop_instance_with_retry(instance_id, ec2_client)
        
        if success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Jupyter notebook execution completed',
                    'command_id': command_id,
                    'instance_id': instance_id,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
            }
        else:
            return create_error_response("노트북 실행 실패 또는 타임아웃")
            
    except Exception as e:
        print(f"❌ Lambda 실행 오류: {e}")
        return create_error_response(f"Lambda 오류: {str(e)}")


def create_client_with_retry(service_name, access_key, secret_key, config, max_retries=3):
    """AWS 클라이언트 생성 (재시도 로직)"""
    for attempt in range(max_retries):
        try:
            print(f"🔌 {service_name} 클라이언트 생성 시도 {attempt + 1}/{max_retries}")
            
            client = boto3.client(
                service_name,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=config
            )
            
            # 간단한 API 호출로 연결 테스트
            if service_name == "ec2":
                client.describe_regions(RegionNames=[config.region_name])
            elif service_name == "ssm":
                client.describe_instance_information(MaxResults=5)
            
            print(f"✅ {service_name} 클라이언트 생성 성공")
            return client
            
        except (ConnectTimeoutError, ReadTimeoutError) as e:
            print(f"⚠️ {service_name} 연결 타임아웃 (시도 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"⏳ {wait_time}초 대기 후 재시도...")
                time.sleep(wait_time)
            else:
                print(f"❌ {service_name} 클라이언트 생성 최종 실패")
                return None
        except Exception as e:
            print(f"❌ {service_name} 클라이언트 생성 오류: {e}")
            return None
    
    return None


def start_instance_with_retry(instance_id, ec2_client, max_retries=3):
    """인스턴스 시작 (재시도 로직)"""
    for attempt in range(max_retries):
        try:
            print(f"🚀 인스턴스 시작 시도 {attempt + 1}/{max_retries}")
            
            # 현재 상태 확인
            response = ec2_client.describe_instances(InstanceIds=[instance_id])
            current_state = response['Reservations'][0]['Instances'][0]['State']['Name']
            print(f"📊 현재 상태: {current_state}")
            
            if current_state == 'running':
                print("✅ 인스턴스가 이미 실행 중")
                return True
            elif current_state in ['stopped', 'stopping']:
                ec2_client.start_instances(InstanceIds=[instance_id])
                print("✅ 인스턴스 시작 요청 완료")
                return True
            else:
                print(f"⚠️ 예상치 못한 상태: {current_state}")
                time.sleep(10)
                
        except (ConnectTimeoutError, ReadTimeoutError) as e:
            print(f"⚠️ 인스턴스 시작 타임아웃 (시도 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(15)
            else:
                print("❌ 인스턴스 시작 최종 실패")
                return False
        except Exception as e:
            print(f"❌ 인스턴스 시작 오류: {e}")
            time.sleep(10)
    
    return False


def wait_for_instance_ready(instance_id, ec2_client, ssm_client, max_wait=300):
    """인스턴스 및 SSM 준비 대기"""
    print("⏳ 인스턴스 및 SSM Agent 준비 대기 중...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            # EC2 상태 확인
            response = ec2_client.describe_instance_status(
                InstanceIds=[instance_id],
                IncludeAllInstances=True
            )
            
            if response['InstanceStatuses']:
                instance_state = response['InstanceStatuses'][0]['InstanceState']['Name']
                system_status = response['InstanceStatuses'][0].get('SystemStatus', {}).get('Status', 'not-applicable')
                instance_status = response['InstanceStatuses'][0].get('InstanceStatus', {}).get('Status', 'not-applicable')
                
                print(f"📊 상태 - Instance: {instance_state}, System: {system_status}, Instance: {instance_status}")
                
                if instance_state == 'running':
                    # SSM Agent 확인
                    try:
                        ssm_response = ssm_client.describe_instance_information(
                            Filters=[{'Key': 'InstanceIds', 'Values': [instance_id]}]
                        )
                        
                        if ssm_response['InstanceInformationList']:
                            ping_status = ssm_response['InstanceInformationList'][0]['PingStatus']
                            print(f"📡 SSM 상태: {ping_status}")
                            
                            if ping_status == 'Online':
                                print("✅ 인스턴스 및 SSM Agent 준비 완료")
                                return True
                        else:
                            print("⏳ SSM Agent 정보 없음")
                    except Exception as ssm_error:
                        print(f"⚠️ SSM 상태 확인 오류: {ssm_error}")
            
            time.sleep(15)
            
        except (ConnectTimeoutError, ReadTimeoutError) as e:
            print(f"⚠️ 상태 확인 타임아웃: {e}")
            time.sleep(15)
        except Exception as e:
            print(f"⚠️ 상태 확인 오류: {e}")
            time.sleep(15)
    
    print("❌ 인스턴스 준비 대기 타임아웃")
    return False


def execute_notebook_with_retry(instance_id, ssm_client, max_retries=3):
    """노트북 실행 (재시도 로직)"""
    commands = [
        'cd /home/ubuntu',
        'echo "현재 디렉토리: $(pwd)"',
        'echo "사용자: $(whoami)"',
        'ls -la new-grad.ipynb',
        'jupyter nbconvert --to notebook --execute /home/ubuntu/new-grad.ipynb --output /home/ubuntu/new-grad-out-$(date +%Y%m%d_%H%M%S).ipynb --ExecutePreprocessor.timeout=1800',
        'echo "노트북 실행 완료"'
    ]
    
    for attempt in range(max_retries):
        try:
            print(f"📝 노트북 실행 시도 {attempt + 1}/{max_retries}")
            
            response = ssm_client.send_command(
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": commands},
                InstanceIds=[instance_id],
                TimeoutSeconds=1800,
                CloudWatchOutputConfig={
                    'CloudWatchLogGroupName': 'forecast-trigger-log',
                    'CloudWatchOutputEnabled': True
                }
            )
            
            command_id = response['Command']['CommandId']
            print(f"✅ 노트북 실행 명령 전송 성공: {command_id}")
            
            # 명령 전송 검증
            time.sleep(3)
            try:
                ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
                print("✅ 명령 전송 검증 완료")
                return command_id
            except ClientError as verify_error:
                if 'InvocationDoesNotExist' in str(verify_error):
                    print(f"⚠️ 명령 전송 실패 (시도 {attempt + 1})")
                    continue
                else:
                    return command_id
            
        except (ConnectTimeoutError, ReadTimeoutError) as e:
            print(f"⚠️ 노트북 실행 타임아웃 (시도 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(20)
        except Exception as e:
            print(f"❌ 노트북 실행 오류 (시도 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(20)
    
    print("❌ 노트북 실행 최종 실패")
    return None


def wait_for_completion_with_retry(command_id, instance_id, ssm_client, max_wait=1800):
    """명령 완료 대기 (재시도 로직)"""
    print(f"⏳ 명령 완료 대기 중... (Command ID: {command_id})")
    start_time = time.time()
    consecutive_errors = 0
    
    while time.time() - start_time < max_wait:
        try:
            response = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            
            status = response['Status']
            elapsed = int(time.time() - start_time)
            print(f"📊 명령 상태: {status} ({elapsed}초 경과)")
            
            consecutive_errors = 0  # 성공하면 에러 카운트 리셋
            
            if status == 'Success':
                print("✅ 노트북 실행 완료!")
                return True
            elif status == 'Failed':
                print("❌ 노트북 실행 실패")
                error_content = response.get('StandardErrorContent', '')
                if error_content:
                    print(f"🚨 오류 내용: {error_content[:500]}")
                return False
            elif status in ['Pending', 'InProgress', 'Delayed']:
                time.sleep(30)
            else:
                print(f"❓ 예상치 못한 상태: {status}")
                time.sleep(30)
                
        except (ConnectTimeoutError, ReadTimeoutError) as e:
            consecutive_errors += 1
            print(f"⚠️ 상태 확인 타임아웃 ({consecutive_errors}회 연속): {e}")
            
            if consecutive_errors >= 5:
                print("❌ 연속 타임아웃으로 인한 포기")
                return False
            
            time.sleep(30)
        except Exception as e:
            consecutive_errors += 1
            print(f"⚠️ 상태 확인 오류 ({consecutive_errors}회 연속): {e}")
            
            if consecutive_errors >= 5:
                print("❌ 연속 오류로 인한 포기")
                return False
            
            time.sleep(30)
    
    print("❌ 명령 완료 대기 타임아웃")
    return False


def create_error_response(message):
    """에러 응답 생성"""
    return {
        'statusCode': 500,
        'body': json.dumps({
            'success': False,
            'error': message,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    }
