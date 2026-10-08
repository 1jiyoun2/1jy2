let pyodide = null;
let problem = null;
let starterCode = "";

const codeEl = document.getElementById("code");
const stdinEl = document.getElementById("stdin");
const editor = CodeMirror.fromTextArea(codeEl, {
    mode: "python",
    theme: "material-darker",
    lineNumbers: true,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    lineWrapping: false,
    matchBrackets: true,
    autoCloseBrackets: true
});
const outputEl = document.getElementById("output");
const judgeEl = document.getElementById("judge-result");
const runBtn = document.getElementById("run-btn");
const judgeBtn = document.getElementById("judge-btn");
const resetBtn = document.getElementById("reset-btn");

function normalizeOutput(text) {
    return String(text).replace(/\r\n/g, "\n").trimEnd();
}

async function executePython(code, stdinText) {
    pyodide.globals.set("user_code", code);
    pyodide.globals.set("stdin_text", stdinText);

    const raw = await pyodide.runPythonAsync(`
import builtins
import contextlib
import io
import json

_input_lines = iter(stdin_text.splitlines())

def _practice_input(prompt=""):
    try:
        return next(_input_lines)
    except StopIteration:
        raise EOFError("입력값이 부족합니다.")

_old_input = builtins.input
builtins.input = _practice_input
_buffer = io.StringIO()
_error = None

try:
    with contextlib.redirect_stdout(_buffer):
        exec(user_code, {})
except Exception as e:
    _error = f"{type(e).__name__}: {e}"
finally:
    builtins.input = _old_input

json.dumps({
    "output": _buffer.getvalue(),
    "error": _error
}, ensure_ascii=False)
`);

    return JSON.parse(String(raw));
}

async function loadProblem() {
    const id = new URLSearchParams(location.search).get("id");
    if (!id) throw new Error("문제 번호가 없습니다.");

    const response = await fetch(`problems/${id}.json`);
    if (!response.ok) throw new Error("문제를 찾을 수 없습니다.");
    problem = await response.json();
    starterCode = problem.starter_code || "";

    document.title = `${problem.title} | Coding Practice`;
    document.getElementById("problem-title").textContent = problem.title;
    document.getElementById("problem-subtitle").textContent = `Python · ${problem.category}`;
    document.getElementById("problem-meta").textContent =
        `문제 ${problem.number} · ${problem.category} · 난이도 ${problem.level}`;
    document.getElementById("top-meta").textContent =
        `Python · ${problem.number}`;
    document.getElementById("description").textContent = problem.description;
    document.getElementById("input-desc").textContent = problem.input;
    document.getElementById("output-desc").textContent = problem.output;
    editor.setValue(starterCode);
    stdinEl.value = problem.examples[0]?.input || "";

    const examples = document.getElementById("examples");
    examples.innerHTML = "";
    problem.examples.forEach((ex, index) => {
        const title = document.createElement("p");
        title.textContent = `예제 ${index + 1} 입력`;
        const input = document.createElement("pre");
        input.className = "example";
        input.textContent = ex.input;
        const title2 = document.createElement("p");
        title2.textContent = `예제 ${index + 1} 출력`;
        const output = document.createElement("pre");
        output.className = "example";
        output.textContent = ex.output;
        examples.append(title, input, title2, output);
    });
}

async function preparePython() {
    pyodide = await loadPyodide();
    outputEl.textContent = "준비 완료. 코드를 작성한 뒤 실행해 보세요.";
    runBtn.disabled = false;
    judgeBtn.disabled = false;
}

runBtn.addEventListener("click", async () => {
    if (!pyodide) return;
    outputEl.textContent = "실행 중...";
    try {
        const result = await executePython(editor.getValue(), stdinEl.value);
        outputEl.textContent = result.error || result.output || "(출력 없음)";
    } catch (error) {
        outputEl.textContent = `실행 환경 오류: ${error.message}`;
    }
});

function makeResultValue(label, value, className = "") {
    const row = document.createElement("div");
    row.className = "judge-detail-row";

    const key = document.createElement("span");
    key.className = "judge-detail-label";
    key.textContent = label;

    const content = document.createElement("code");
    content.className = className;
    content.textContent = value || "(없음)";

    row.append(key, content);
    return row;
}

function renderJudgeResults(results, passed, total) {
    judgeEl.innerHTML = "";
    judgeEl.className = "console judge-console";

    const summary = document.createElement("div");
    summary.className = "judge-summary";

    const score = document.createElement("strong");
    score.className = passed === total ? "judge-score pass-text" : "judge-score fail-text";
    score.textContent = passed === total ? "모두 통과" : `${passed} / ${total} 통과`;

    const hint = document.createElement("span");
    hint.textContent = passed === total ? "모든 테스트를 통과했습니다." : "실패한 테스트를 확인하고 코드를 수정해 보세요.";

    summary.append(score, hint);
    judgeEl.appendChild(summary);

    const list = document.createElement("div");
    list.className = "judge-list";

    results.forEach((result, index) => {
        const item = document.createElement("div");
        item.className = `judge-item ${result.ok ? "is-pass" : "is-fail"}`;

        const head = document.createElement("div");
        head.className = "judge-item-head";

        const name = document.createElement("span");
        name.textContent = `테스트 ${index + 1}`;

        const state = document.createElement("strong");
        state.className = result.ok ? "pass-text" : "fail-text";
        state.textContent = result.ok ? "통과" : (result.error ? "실행 오류" : "실패");

        head.append(name, state);
        item.appendChild(head);

        if (!result.ok) {
            const detail = document.createElement("div");
            detail.className = "judge-details";

            if (result.error) {
                detail.appendChild(makeResultValue("오류", result.error, "actual-value"));
            } else {
                detail.appendChild(makeResultValue("입력", result.input));
                detail.appendChild(makeResultValue("기대", result.expected, "expected-value"));
                detail.appendChild(makeResultValue("결과", result.actual, "actual-value"));
            }
            item.appendChild(detail);
        }

        list.appendChild(item);
    });

    judgeEl.appendChild(list);
}

judgeBtn.addEventListener("click", async () => {
    if (!pyodide || !problem) return;
    judgeBtn.disabled = true;
    runBtn.disabled = true;
    judgeEl.className = "console judge-console";
    judgeEl.textContent = "채점 중...";

    const results = [];
    let passed = 0;

    for (let i = 0; i < problem.tests.length; i++) {
        const test = problem.tests[i];
        try {
            const runResult = await executePython(editor.getValue(), test.input);
            const expected = normalizeOutput(test.output);

            if (runResult.error) {
                results.push({
                    ok: false,
                    error: runResult.error
                });
                continue;
            }

            const actual = normalizeOutput(runResult.output);
            const ok = actual === expected;

            if (ok) passed++;

            results.push({
                ok,
                input: test.input,
                expected,
                actual
            });
        } catch (error) {
            results.push({
                ok: false,
                error: error.message
            });
        }
    }

    renderJudgeResults(results, passed, problem.tests.length);
    judgeBtn.disabled = false;
    runBtn.disabled = false;
});

resetBtn.addEventListener("click", () => {
    editor.setValue(starterCode);
    stdinEl.value = problem?.examples[0]?.input || "";
    outputEl.textContent = pyodide ? "초기화했습니다." : "Python 실행 환경을 준비하는 중입니다...";
    judgeEl.textContent = "아직 채점하지 않았습니다.";
    judgeEl.className = "console judge-console";
});

(async () => {
    try {
        await loadProblem();
        await preparePython();
    } catch (error) {
        document.getElementById("problem-title").textContent = "문제를 불러오지 못했습니다.";
        outputEl.textContent = error.message;
    }
})();