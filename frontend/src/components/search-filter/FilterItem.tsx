import { ChangeEvent, useEffect, useRef, useState } from 'react';
import useClickOutside from '../../hooks/useClickOutside';
import { ReactComponent as IconArrowDown } from '../../assets/icons/info/arrow-down.svg';
import useSearchQueryStore from '../../store/search-query';

const FilterItem = ({
  category
}: {
  category: {
    type: string;
    title: string;
    options: { id: string; label: string }[];
  };
}) => {
  const setSearchQueryFilter = useSearchQueryStore((state) => state.setFilter);

  /** 드롭다운 오픈 여부 */
  const [isOpen, setIsOpen] = useState<boolean>(false);

  /** 드롭다운 영역 (버튼 포함) */
  const dropdownRef = useRef<HTMLDivElement>(null);

  /** 드롭다운 영역 밖 클릭 시 닫기 */
  useClickOutside({ ref: dropdownRef, callback: () => setIsOpen(false) });

  /** 체크한 값들 관리 */
  const [selectedOptions, setSelectedOptions] = useState<{
    [key: string]: boolean;
  }>({});

  /** input onChange 핸들러 */
  const handleCheckboxChange = (id: string, e: ChangeEvent<HTMLInputElement>) => {
    setSelectedOptions((prev) => {
      // input type === 'checkbox'인 경우
      if (category.type === 'chargerTypes') {
        return {
          ...prev,
          [id]: e.target.checked
        };
      }
      // input type === 'radio'인 경우
      else {
        return {
          [id]: e.target.checked
        };
      }
    });
  };

  /** 체크한 값 상태 변경 시 전역 검색필터 쿼리 업데이트 */
  useEffect(() => {
    // 체크된 항목 id만 추출
    const selectedItems: string[] = Object.keys(selectedOptions).filter((key) => selectedOptions[key]);

    // 전역 검색필터 쿼리 업데이트
    setSearchQueryFilter(category.type, selectedItems);
  }, [selectedOptions]);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* 카테고리 버튼 */}
      <div
        className="rounded-md border border-[#D6DAE1] pl-3 pr-2 py-1 flex flex-shrink-0 items-center justify-center gap-1 cursor-pointer"
        key={category.type}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="flex gap-1 items-center text-black-light text-sm font-light">
          <span>{category.title}</span>
          {isOpen ? (
            <IconArrowDown width={16} fill="#535353" style={{ transform: 'rotate(180deg)' }} />
          ) : (
            <IconArrowDown width={16} fill="#535353" />
          )}
        </span>
      </div>
      {/* 드롭다운 (체크박스 목록) */}
      {isOpen && (
        <div className="absolute p-4 top-[100%] left-0 bg-white flex flex-col gap-2 z-[2] rounded-b-lg w-max min-w-full shadow-lg text-black-light text-sm">
          {category.options.map((option) => {
            return (
              <span className="flex gap-1" key={option.id}>
                <input
                  type={category.type === 'chargerTypes' ? 'checkbox' : 'radio'}
                  id={option.id}
                  value={option.id}
                  name={category.type}
                  checked={selectedOptions[option.id] || false}
                  onChange={(e) => handleCheckboxChange(option.id, e)}
                ></input>
                <label htmlFor={option.id}>{option.label}</label>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FilterItem;
