<img width="1920" height="1080" alt="EVolution_banner" src="https://github.com/user-attachments/assets/bf65940d-c489-4ae9-a446-a60d147984cf" />

## ✨ 프로젝트 소개
전기차 보급 증가에 따라 충전소 검색서비스가 늘어나고 있지만, 사용자들이 충전소 이용 시 겪는 불편함이 여전히 존재합니다.
<br>기존 서비스들은 충전소 위치와 충전기 상태, 요금 등 기본 정보를 제공하지만, 예상 대기시간, 방문객 분포, 교통상황 같은 실질적인 편의 정보는 부족하여 사용자가 최적의 충전소를 선택하는 데 어려움이 있습니다.
<br><br>이에, 단순히 충전소 정보만을 파악하는 것을 넘어, 실시간 충전소 수요예측, 도로교통상황 표시 기능 등을 제공하여, 사용자의 충전소 검색 편의성과 만족도를 향상시킨 서비스를 기획하였습니다.

> 2024년 충남대학교 졸업 프로젝트<br>
> 2024년 대전 공공데이터 활용 창업경진대회 제품 및 서비스 개발부문 본선진출작

## 🚀 주요 기능
### 1. 주변 충전소 검색 및 각 충전소의 사용가능여부 표시
서비스 초기 화면에 접속하면, 사용자 디바이스의 GPS를 활용하여 현재 위치를 파악한 다음, 주변 전기차 충전소들의 위치와 사용가능 여부를 지도 상의 마커(marker) 형태로 표시합니다.<br>
또한 지도 상단의 '실시간교통' 버튼을 활성화하면 카카오맵 서버에서 제공하는 도로 교통 상황을 제공받을 수 있습니다.
### 2. 최근 30분내 출발자수 수집을 위한 충전소 경로안내 기능
검색된 주변 충전소들 중 하나를 선택하면 하단에 간략한 충전소 정보와 함께, 해당 충전소까지의 경로 안내를 받는 '경로안내' 버튼이 있습니다.<br>
사용자가 특정 충전소에 대해 경로안내 버튼을 눌러 3rd-party 내비게이션 서비스로 이동하면, 본 서비스에서는 이를 사용자가 해당 충전소를 곧 사용하기 위해 출발했을 가능성이 높다고 판단하고, 30분내 출발기록 데이터로 처리하여 1시간 동안의 예상방문자수, 예상혼잡도 계산기능에 활용합니다.
### 3. 충전소에 대해 앞으로 1시간 동안의 예상방문자수, 예상혼잡도 표시
각 충전소에 대해 지난 30일동안의 30분 간격의 방문자수 데이터를 수집하여 수집시각(time)과 방문자수(visitNum)의 시계열 데이터로 정제한 후, RandomForest 모델을 활용하여 당일 0시~23시의 시간당 방문자수를 예측합니다.<br>
충전소 방문 데이터에 대한 다음 4가지 항목들을 바탕으로 각기 다른 가중치를 설정하여 최종적으로 앞으로 1시간 동안의 예상방문자수와 예상혼잡도를 계산합니다.
- 충전소에서 현재 사용중인 충전기 대수
- 30분 내 해당 충전소로 출발한 고객수
- 30일 동안의 방문자수 데이터를 바탕으로 예측한 방문자수
- 실시간 충전소 상세정보 조회수
  
충전소 상세정보 페이지에서 예상방문자수 및 혼잡여부, 그리고 수요예측 모델로 예상한 당일 시간당 방문자수 그래프를 확인할 수 있습니다.

## 🧩 시스템 아키텍처
### 개선 전 아키텍처
<img width="100%" alt="image" src="https://github.com/user-attachments/assets/fcd76672-b99d-4c08-9c3a-4144dd782433" />

### 개선 예정 아키텍처 (2025.09~)
- Blue Green 무중단 배포 및 배포 자동화 CI/CD 파이프라인 구축
- Public Subnet(API 서버), Private Subnet(DB, ML용 인스턴스, Lambda) 분리
- AWS Lambda, EventBridge, SSM을 활용하여 충전소 데이터 수집 및 수요예측 자동화
<img width="1373" height="999" alt="image" src="https://github.com/user-attachments/assets/edeb066c-419f-4b94-9f05-be26ac9388c9" />

<br>

## 🫶🏻 팀 소개

<table align="center">
  <tr>
    <th><a href="https://github.com/minsuhan1">한민수</a></th>
    <th><a href="https://github.com/mandarinnn2">김연송</a></th>
    <th><a href="https://github.com/jungsehui">정세희</a></th>
  </tr>
  <tr>
    <td><img src="https://avatars.githubusercontent.com/u/50696567?v=4" width="120" height="120"></td>
    <td><img src="https://avatars.githubusercontent.com/u/50360362?v=4" width="120" height="120"></td>
    <td><img src="https://avatars.githubusercontent.com/u/116075689?v=4" width="120" height="120"></td>
  </tr>
  <tr align="center">
    <td>Frontend<br>Backend</td>
    <td>Backend<br>Machine Learning</td>
    <td>Backend</td>
  </tr>
</table>
