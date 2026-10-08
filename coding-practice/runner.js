let pyodide = null;
let problem = null;
let starterCode = "";

const codeEl = document.getElementById("code");
const stdinEl = document.getElementById("stdin");
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

    return await pyodide.runPythonAsync(`
import builtins
import contextlib
import io

_input_lines = iter(stdin_text.splitlines())

def _practice_input(prompt=""):
    try:
        return next(_input_lines)
    except StopIteration:
        raise EOFError("입력값이 부족합니다.")

_old_input = builtins.input
builtins.input = _practice_input
_buffer = io.StringIO()

try:
    with contextlib.redirect_stdout(_buffer):
        exec(user_code, {})
    _practice_result = _buffer.getvalue()
except Exception as e:
    _practice_result = f"{type(e).__name__}: {e}"
finally:
    builtins.input = _old_input

_practice_result
`);
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
    document.getElementById("description").textContent = problem.description;
    document.getElementById("input-desc").textContent = problem.input;
    document.getElementById("output-desc").textContent = problem.output;
    codeEl.value = starterCode;
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
        const result = await executePython(codeEl.value, stdinEl.value);
        outputEl.textContent = String(result) || "(출력 없음)";
    } catch (error) {
        outputEl.textContent = `실행 환경 오류: ${error.message}`;
    }
});

judgeBtn.addEventListener("click", async () => {
    if (!pyodide || !problem) return;
    judgeBtn.disabled = true;
    runBtn.disabled = true;
    judgeEl.textContent = "채점 중...";

    const lines = [];
    let passed = 0;

    for (let i = 0; i < problem.tests.length; i++) {
        const test = problem.tests[i];
        try {
            const actual = normalizeOutput(await executePython(codeEl.value, test.input));
            const expected = normalizeOutput(test.output);
            if (actual === expected) {
                passed++;
                lines.push(`테스트 ${i + 1}: 통과`);
            } else {
                lines.push(
                    `테스트 ${i + 1}: 실패\n  입력: ${test.input.replace(/\n/g, " / ")}\n  기대: ${expected.replace(/\n/g, " / ")}\n  결과: ${actual.replace(/\n/g, " / ")}`
                );
            }
        } catch (error) {
            lines.push(`테스트 ${i + 1}: 실행 오류 - ${error.message}`);
        }
    }

    judgeEl.textContent = `${passed} / ${problem.tests.length} 통과\n\n${lines.join("\n")}`;
    judgeEl.className = passed === problem.tests.length ? "pass" : "fail";
    judgeBtn.disabled = false;
    runBtn.disabled = false;
});

resetBtn.addEventListener("click", () => {
    codeEl.value = starterCode;
    stdinEl.value = problem?.examples[0]?.input || "";
    outputEl.textContent = pyodide ? "초기화했습니다." : "Python 실행 환경을 준비하는 중입니다...";
    judgeEl.textContent = "아직 채점하지 않았습니다.";
    judgeEl.className = "";
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