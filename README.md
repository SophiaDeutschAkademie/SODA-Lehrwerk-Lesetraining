# SODA LESETRAINING

Sophia Deutsch Akademie의 독일어 독해 훈련 웹앱입니다. 표지 → 레벨 선택(A1–C1) → 레벨별 텍스트 목록 → 읽기 화면으로 구성돼요.

읽기 화면은 네 개의 탭으로 나뉘어요.

- **본문 (Text)**: 독일어 텍스트와 단락별 한국어 해석(눌러서 보기)
- **문제 (Aufgaben)**: 본문 표현을 바꿔 말한(패러프레이징) 독해 문제. 채점하면 정답 근거 문장, ‘본문 표현 → 문제 표현’ 대응, 해설이 나와요. ‘본문에서 보기’를 누르면 근거 문장이 본문에 표시돼요.
- **문법 (Grammatik)**: 본문 문장으로 정리한 주요 문법과 문장 성분 분석
- **어휘 (Wortschatz)**: 단어와 숙어·표현 (뜻 가리기 기능)

글자 크기 조절과 인쇄(본문·문제·문법·어휘를 차례로 출력, 해석과 정답은 펼친 경우에만 출력) 기능이 있어요.

## GitHub Pages로 배포하기

1. 저장소의 **Settings → Pages**에서 Source를 `Deploy from a branch`, Branch를 `main` / `/ (root)`로 지정하고 Save를 누릅니다.
2. 1~2분 뒤 `https://sophiadeutschakademie.github.io/SODA-Lehrwerk-Lesetraining/` 주소로 접속됩니다.

`.nojekyll` 파일은 숨김 파일이라 폴더에서 안 보일 수 있어요. 지우지 마세요.

## 구조

- `index.html` : 앱 화면 (표지, 레벨 선택, 목록, 읽기 화면을 한 페이지 안에서 전환)
- `assets/` : 화면 스타일(`app.css`), 동작(`app.js`), 로고, 아이콘, 글꼴 (인터넷 연결 없이도 동작)
- `data/` : 앱이 읽는 데이터 (`index.js`, `a1.js` … `c1.js`) — 직접 고치지 말고 아래 방법으로 다시 만들어요.
- `src/texts/` : 텍스트 원본 50개 (`a1-01.json` … `c1-10.json`)
- `tools/validate.py` : 원본 검사 (근거 문장이 본문과 일치하는지, 문항 수, 형식, 객관식 선지 길이 등)
- `tools/build.py` : 원본으로 `data/` 파일을 다시 만듦

## 텍스트 고치기·추가하기

1. `src/texts/` 의 JSON 파일을 고치거나 새 파일을 추가합니다. (형식은 기존 파일과 같게)
2. 터미널에서 저장소 폴더로 이동한 뒤 실행합니다.

   ```
   python3 tools/validate.py
   python3 tools/build.py
   ```

3. 바뀐 `src/texts/` 파일과 `data/` 파일을 함께 올립니다.

본문 문장을 고치면 그 문장을 인용한 문제 근거(`evidence`), 문법 예문, 숙어 예문도 같은 문장으로 고쳐야 해요. `validate.py`가 맞지 않는 곳을 알려 줘요.

객관식 선지는 길이가 서로 비슷해야 해요(가장 긴 선지÷가장 짧은 선지 ≤ 1.2). 정답만 길어서 눈에 띄는 일이 없게 하려는 규칙이고, 어긋나면 `validate.py`가 오류로 알려 줘요. 이름을 고르는 연결하기 문항은 제외해요.

### JSON 주요 항목

| 항목 | 내용 |
|---|---|
| `title`, `titleKo`, `type`, `typeKo`, `intro`, `focus` | 제목, 글 종류, 목록 카드 설명, 문법 태그 |
| `paragraphs` | 단락 목록. `de`(독일어), `ko`(해석), `label`(말한 사람·광고 이름), `style`(`h` 소제목, `q` 인터뷰 질문, `meta` 인사·서명) |
| `questions` | `type`: `rf`(Richtig/Falsch), `rfn`(Ja/Nein/Text sagt dazu nichts), `mc`(선택형) · `answer`: 정답 번호(0부터) · `evidence`: 본문 근거(본문과 글자 하나까지 같아야 함) · `pairs`: [본문 표현, 문제 표현] · `explain`: 해설 |
| `grammar` | `title`, `term`, `explain`, `pattern`, `examples`(`de` 본문 문장, `ko`, `mark` 강조 부분, `parts` 문장 성분), `tip` |
| `vocab`, `phrases` | 단어(`de`, `ko`), 숙어·표현(`de`, `ko`, `ex` 본문 예문, `exko`) |
