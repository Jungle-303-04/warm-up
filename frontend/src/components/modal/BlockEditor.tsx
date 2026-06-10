import type { BlockInput, BlockType } from "../../types/page";

type BlockEditorProps = {
  blocks: BlockInput[];
  onChange: (blocks: BlockInput[]) => void;
};

// select 박스에 보여줄 본문 블록 종류입니다.
const BLOCK_TYPES: { label: string; value: BlockType }[] = [
  { label: "문단", value: "PARAGRAPH" },
  { label: "제목", value: "HEADING" },
  { label: "불릿", value: "BULLET" },
  { label: "체크리스트", value: "CHECKLIST" },
  { label: "코드", value: "CODE" },
];

export function BlockEditor({ blocks, onChange }: BlockEditorProps) {
  const updateBlock = (index: number, nextBlock: Partial<BlockInput>) => {
    // 특정 index의 블록만 새 값으로 바꾸고 나머지 블록은 그대로 둡니다.
    const nextBlocks = blocks.map((block, blockIndex) => {
      if (blockIndex !== index) {
        return block;
      }

      return {
        ...block,
        ...nextBlock,
      };
    });

    onChange(nextBlocks);
  };

  const addBlock = () => {
    // 새 블록은 기본 문단(PARAGRAPH)으로 추가합니다.
    onChange([
      ...blocks,
      {
        type: "PARAGRAPH",
        content: "",
        checked: null,
      },
    ]);
  };

  const deleteBlock = (index: number) => {
    // 삭제 버튼을 누른 블록만 목록에서 제거합니다.
    const nextBlocks = blocks.filter((_, blockIndex) => blockIndex !== index);
    onChange(nextBlocks);
  };

  const handleTypeChange = (index: number, type: BlockType) => {
    // 체크리스트 블록만 checked 값을 쓰고, 나머지 타입은 null로 맞춥니다.
    updateBlock(index, {
      type,
      checked: type === "CHECKLIST" ? false : null,
    });
  };

  return (
    <div className="block-editor">
      <div className="block-editor-header">
        <h3>본문 블록</h3>
        <button type="button" onClick={addBlock}>
          + 블록 추가
        </button>
      </div>

      {blocks.length === 0 && (
        <p className="block-empty">아직 작성된 블록이 없습니다.</p>
      )}

      <div className="block-list">
        {blocks.map((block, index) => (
          <div key={index} className="block-row">
            <div className="block-row-toolbar">
              <select
                value={block.type}
                onChange={(event) =>
                  handleTypeChange(index, event.target.value as BlockType)
                }
              >
                {BLOCK_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>

              <button
                type="button"
                className="block-delete-button"
                onClick={() => deleteBlock(index)}
              >
                삭제
              </button>
            </div>

            {block.type === "CHECKLIST" ? (
              <div className="check-block-input">
                <input
                  type="checkbox"
                  checked={block.checked ?? false}
                  onChange={(event) =>
                    updateBlock(index, {
                      checked: event.target.checked,
                    })
                  }
                />

                <input
                  value={block.content}
                  placeholder="체크리스트 내용을 입력하세요"
                  onChange={(event) =>
                    updateBlock(index, {
                      content: event.target.value,
                    })
                  }
                />
              </div>
            ) : (
              <textarea
                className={block.type === "CODE" ? "code-textarea" : ""}
                value={block.content}
                placeholder="내용을 입력하세요"
                rows={block.type === "HEADING" ? 2 : 4}
                onChange={(event) =>
                  updateBlock(index, {
                    content: event.target.value,
                  })
                }
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
