document.addEventListener('DOMContentLoaded', () => {
    const blocks = document.querySelectorAll('.code-embed[data-src]');

    blocks.forEach(async (block) => {
        const src = block.dataset.src;
        const label = block.dataset.label || src.split('/').pop();

        block.innerHTML = '';

        const viewer = document.createElement('section');
        viewer.className = 'code-viewer';

        const header = document.createElement('div');
        header.className = 'code-viewer-header';

        const name = document.createElement('span');
        name.textContent = label;

        const actions = document.createElement('div');
        actions.className = 'code-viewer-actions';

        const sourceLink = document.createElement('a');
        sourceLink.href = src;
        sourceLink.textContent = '파일 열기';
        sourceLink.target = '_blank';
        sourceLink.rel = 'noopener';

        const copyButton = document.createElement('button');
        copyButton.type = 'button';
        copyButton.textContent = '복사';

        actions.append(sourceLink, copyButton);
        header.append(name, actions);

        const pre = document.createElement('pre');
        const code = document.createElement('code');
        code.textContent = '코드를 불러오는 중...';
        pre.appendChild(code);

        viewer.append(header, pre);
        block.appendChild(viewer);

        try {
            const response = await fetch(src);
            if (!response.ok) throw new Error('load failed');
            const source = await response.text();
            code.textContent = source;

            copyButton.addEventListener('click', async () => {
                await navigator.clipboard.writeText(source);
                copyButton.textContent = '복사됨';
                setTimeout(() => copyButton.textContent = '복사', 1200);
            });
        } catch (error) {
            code.textContent = '코드를 불러오지 못했습니다.';
            copyButton.disabled = true;
        }
    });
});
