/**
 * Generate only the public 1jy2.com static-site artifact.
 * This is a deterrent against casual code inspection, NOT encryption or access control.
 * The original GitHub repository remains public until its visibility is changed separately.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(repoRoot, "_site");
const publicInputs = [
    "CNAME",
    "index.html",
    "site-home.js",
    "archive",
    "class-board",
    "coding-practice",
    "courses",
    "tools/transkun"
];
const sensitivePatterns = [
    ["Supabase secret key", /\bsb_secret_[a-zA-Z0-9_-]{12,}/],
    ["GitHub access token", /\b(?:ghp_|github_pat_)[a-zA-Z0-9_]{20,}/],
    ["OpenAI secret key", /\bsk-(?:proj-)?[a-zA-Z0-9_-]{20,}/],
    ["Private key", /-----BEGIN [A-Z ]*PRIVATE KEY-----/]
];
const forbiddenBasenames = new Set([".env", ".env.local", ".DS_Store"]);
const forbiddenExtensions = new Set([".map", ".pem", ".key", ".p12"]);
let minifyPackage = null;
const statistics = { copied: 0, html: 0, js: 0, bytesIn: 0, bytesOut: 0 };

async function minifyJavaScript(source, label, module = false) {
    if (process.env.BUILD_SKIP_MINIFY === "1") return source;
    if (!minifyPackage) minifyPackage = await import("terser");
    const result = await minifyPackage.minify(source, {
        module,
        compress: { passes: 2 },
        mangle: true,
        format: { comments: "some", ascii_only: false }
    });
    if (result.error || typeof result.code !== "string") {
        throw new Error("JavaScript minification failed: " + label);
    }
    return result.code;
}

async function minifyInlineScripts(html, filename) {
    const pattern = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
    const matches = [...html.matchAll(pattern)];
    let result = html;
    for (const match of matches.reverse()) {
        const attributes = match[1];
        const type = attributes.match(/\btype\s*=\s*["']([^"']+)["']/i)?.[1]?.toLowerCase() || "";
        if (/\bsrc\s*=/.test(attributes) || (type && !["text/javascript", "application/javascript", "module"].includes(type))) continue;
        if (!match[2].trim()) continue;
        const minified = await minifyJavaScript(match[2], filename + " inline-script", type === "module");
        result = result.slice(0, match.index) + "<script" + attributes + ">" + minified + "</script>" + result.slice(match.index + match[0].length);
    }
    return result;
}

function scanForSecrets(value, sourcePath) {
    for (const [description, regex] of sensitivePatterns) {
        if (regex.test(value)) throw new Error("Blocked sensitive material (" + description + "): " + sourcePath);
    }
}

async function copyPublicPath(relativePath) {
    const source = path.join(repoRoot, relativePath);
    const target = path.join(outputDir, relativePath);
    const stat = await fs.lstat(source);
    if (stat.isSymbolicLink()) throw new Error("Symbolic link disallowed in public artifact: " + relativePath);
    if (stat.isDirectory()) {
        await fs.mkdir(target, { recursive: true });
        for (const item of (await fs.readdir(source)).sort()) {
            if (item.startsWith(".") || item === "node_modules" || item === "__pycache__") continue;
            await copyPublicPath(path.posix.join(relativePath, item));
        }
        return;
    }
    if (!stat.isFile()) return;
    const basename = path.basename(relativePath);
    if (forbiddenBasenames.has(basename) || forbiddenExtensions.has(path.extname(basename).toLowerCase())) {
        throw new Error("File blocked from public artifact: " + relativePath);
    }
    await fs.mkdir(path.dirname(target), { recursive: true });
    if (/\.(?:html?|js|json|css|py|ipynb|md|txt)$/i.test(relativePath)) {
        let data = await fs.readFile(source, "utf8");
        scanForSecrets(data, relativePath);
        const oldSize = Buffer.byteLength(data);
        if (relativePath.endsWith(".js")) {
            data = await minifyJavaScript(data, relativePath);
            statistics.js++;
        } else if (relativePath.endsWith(".html")) {
            data = await minifyInlineScripts(data, relativePath);
            statistics.html++;
        }
        await fs.writeFile(target, data, "utf8");
        statistics.bytesIn += oldSize;
        statistics.bytesOut += Buffer.byteLength(data);
    } else {
        await fs.copyFile(source, target);
    }
    statistics.copied++;
}

if (outputDir === repoRoot || !outputDir.startsWith(repoRoot + path.sep)) throw new Error("Unsafe output directory");
await fs.rm(outputDir, { recursive: true, force: true });
await fs.mkdir(outputDir, { recursive: true });
for (const item of publicInputs) await copyPublicPath(item);
await fs.writeFile(path.join(outputDir, ".nojekyll"), "", "utf8");
const expected = ["index.html", "class-board/index.html", "coding-practice/runner.js", "coding-practice/problems/index.json"];
for (const p of expected) await fs.access(path.join(outputDir, p));
for (const p of ["projects/music-ai/analyze.py", "scripts/build-site.mjs", ".github/workflows/secure-pages.yml"]) {
    try {
        await fs.access(path.join(outputDir, p));
        throw new Error("Private/development source accidentally published: " + p);
    } catch (error) {
        if (error.code !== "ENOENT") throw error;
    }
}
console.log("Secure Pages build completed:", JSON.stringify(statistics));
