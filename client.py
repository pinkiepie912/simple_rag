import time
import requests
import pprint
from pathlib import Path

UPLOAD_URL = "http://localhost:8000/api/v1/docs/upload-url"
GET_DOCS_URL = "http://localhost:8000/api/v1/docs"
QUESTION_URL = "http://localhost:8000/api/v1/docs/question"

# sample_files 디렉터리 설정
BASE_DIR = Path(__file__).parent
SAMPLE_DIR = BASE_DIR / "sample_files"

QUESTION_MAP = {
    "pptx": "나는 하루 종일 스마트폰 알림에 반응하느라 정작 중요한 업무에 집중하지 못하는 상태에 점점 익숙해지고 있어. 특히 유튜브, 인스타그램, 메신저 알림이 계속 들어오다 보니 몇 분 이상 깊이 몰입하는 게 힘들고, 퇴근 후에도 머리가 지친 느낌이야. 이런 디지털 과잉 자극에서 벗어나기 위해 디지털 미니멀리즘이라는 개념이 제안된 걸로 알고 있는데, 구체적으로 이 철학이 어떤 원칙에 기반하고 있고, 어떤 실천 전략들을 통해 내가 일상에서 주도권을 되찾을 수 있을지 알려줘. 그리고 사람들이 자주 실패하는 이유도 함께 분석해줘.",
    
    "docx": "나는 현재 초기 스타트업을 운영 중인데, 제품은 어느 정도 완성되었지만 고객 반응이 미미하고, 팀 내 커뮤니케이션도 자주 어긋나고 있어. 특히 고객이 무엇을 원하는지를 명확히 알지 못한 채 기능만 계속 추가하다 보니 방향성이 점점 흐려지는 것 같아. 스타트업이 실패하는 결정적 이유 중 ‘시장 없음’, ‘고객 피드백 무시’, ‘현금 흐름 관리 실패’에 해당하는 내 상황을 개선하려면 어떤 실질적인 조치와 학습 루프를 적용해야 하는지 전략적으로 조언해줘.",
    
    "txt": "나는 혼자 디지털 제품을 만드는 1인 창업가로, 마케팅, 결제, 고객 관리까지 모든 과정을 수동으로 처리하고 있어서 너무 많은 시간을 소모하고 있어. 글에서 제안된 자동화 흐름(고객 접점, 콘텐츠 배포, 결제 흐름, 고객 피드백 루프 등)을 기반으로 나에게 맞는 자동화 전략을 단계별로 설명해주고, 각 단계에서 어떤 도구를 어떻게 연동하면 좋은지 실제 사례 중심으로 구체적으로 설명해줘. 특히 나는 코딩 경험이 적기 때문에 노코드 중심의 접근을 원해.",
    
    "json": "AI 기반 업무 도구들이 너무 다양해서 어떤 걸 선택해야 할지 혼란스러워. JSON으로 정리된 도구 리스트를 보니 카테고리와 대상, 무료 여부 등이 구체적으로 나와 있는데, 마케터 입장에서 이 도구 중 어떤 조합으로 업무 자동화를 구축하면 가장 효율적인지 추천해주고, 그 이유와 함께 각 도구의 역할 분담 및 데이터 흐름까지 설계해줘. 특히 이메일 마케팅과 콘텐츠 스케줄링 중심으로 알고 싶어.",

    "pdf": "최근 한국 정부와 지자체가 업사이클링(새활용) 산업을 육성하고 지원하기 위해 다양한 법·제도 및 지원 사업을 추진하고 있는 것으로 알고 있습니다. 특히 환경부의 ‘자원순환기본계획(2018~2027)’과 새활용 기업에 대한 맞춤형 지원 프로그램, 새활용 센터 설립 및 운영, 인증마크 도입 검토 등의 흐름이 인상 깊었습니다. 하지만 보고서를 보면 여전히 소비자 입장에서 새활용 제품의 시장 접근성이 낮고, 안전성 및 신뢰성에 대한 우려가 커서 실제 구매 경험은 낮은 것으로 나타납니다. 이런 배경에서, 정부나 공공기관이 새활용 시장을 활성화하기 위해 반드시 고려해야 할 소비자 중심의 실질적 정책 방안에는 어떤 것들이 있으며, 특히 새활용 제품에 대한 인식 개선과 실제 시장 진입 장벽을 낮추는 전략을 설계한다면 구체적으로 어떤 요소(홍보, 인증, 유통, 교육, 체험 인프라 등)를 우선시해야 하는지 단계별로 정리해줄 수 있을까요?",

    "py": "이 문서에는 외부 텍스트 파일을 불러와서 특정 방식으로 분할한 뒤 Elasticsearch에 저장하는 전체 파이프라인이 구현되어 있다고 들었어. 이 중에서 '텍스트를 청크로 분리'하거나 'Elasticsearch에 색인'하는 과정에 대한 함수 정의 부분만 골라서 보여줘. 그리고 해당 함수들이 호출되는 순서까지 코드 흐름으로 설명해줘."

}



def get_file_info(file_path: Path) -> tuple[str, int]:
    extension = file_path.suffix.replace(".", "").lower()
    size = file_path.stat().st_size
    return extension, size

def upload_all_files():
    if not SAMPLE_DIR.exists():
        raise FileNotFoundError(f"디렉터리가 존재하지 않습니다: {SAMPLE_DIR}")

    for file_path in SAMPLE_DIR.iterdir():
        if file_path.is_file():
            ext, size = get_file_info(file_path)
            print(f"파일명: {file_path.name} | 확장자: {ext} | 크기: {size} bytes")
            
            print(f"S3 Upload url 요청...")
            res = requests.post(UPLOAD_URL, json={
                "filename": file_path.name,
                "size": size,
            })
            data = res.json()
            presigned_url = data.get("presignedUrl")
            metadata = data.get("metadata")
            doc_id = metadata.get("docId")
            print(f"PresignedUrl: {presigned_url} | Metadata: {metadata}")
        
            
            print(f"파일 업로드...")
            with open(file_path, "rb") as f:
                headers = {
                    "x-amz-meta-docId": doc_id
                }
                response = requests.put(presigned_url.replace("localstack", "localhost"), data=f, headers=headers)
                response.raise_for_status()
                print(f"업로드 성공: {file_path.name}")

            time.sleep(1)
            print(f"파일 인덱싱 상태 확인...")
            status = None
            while True:
                res = requests.get(GET_DOCS_URL + f"/{doc_id}")
                data = res.json()

                if (data["status"] != "UPLOADED"):
                    status = data["status"]
                    break

                print(f"파일 인덱싱 상태: {data['status']}")
                time.sleep(1)
            
            if status != "INDEXED":
                print(f"파일 인덱싱 실패: {file_path.name} (상태: {status})")
                continue
            print("파일 인덱싱 완료")


            print("질문 응답 요청...")
            question = QUESTION_MAP[ext]
            print(f"문서ID: {doc_id}\n질문: {question}")

            res = requests.post(QUESTION_URL, json={
                "docId": doc_id,
                "question": question
            })
            data = res.json()
            
            print("응답")
            pprint.pprint(data)

            print("\n\n")
        else:
            pass

if __name__ == "__main__":
    upload_all_files()

