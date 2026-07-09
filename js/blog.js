(function () {
    function setActiveTocLink(links, id) {
        links.forEach((link) => {
            const active = link.hash === "#" + id;
            link.classList.toggle("active", active);
            if (active) {
                link.setAttribute("aria-current", "true");
            } else {
                link.removeAttribute("aria-current");
            }
        });
    }

    function initToc() {
        const toc = document.querySelector("[data-blog-toc]");
        if (!toc) {
            return;
        }

        const links = Array.from(toc.querySelectorAll('a[href^="#"]'));
        const headings = links
            .map((link) => document.getElementById(decodeURIComponent(link.hash.slice(1))))
            .filter(Boolean);

        if (!links.length || !headings.length) {
            return;
        }

        const byId = new Map(headings.map((heading) => [heading.id, heading]));
        links.forEach((link) => {
            link.addEventListener("click", () => {
                const id = decodeURIComponent(link.hash.slice(1));
                if (byId.has(id)) {
                    setActiveTocLink(links, id);
                }
            });
        });

        if (!("IntersectionObserver" in window)) {
            setActiveTocLink(links, headings[0].id);
            return;
        }

        const visible = new Map();
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        visible.set(entry.target.id, entry.boundingClientRect.top);
                    } else {
                        visible.delete(entry.target.id);
                    }
                });

                if (visible.size) {
                    const activeId = Array.from(visible.entries())
                        .sort((a, b) => Math.abs(a[1]) - Math.abs(b[1]))[0][0];
                    setActiveTocLink(links, activeId);
                    return;
                }

                const fallback = headings
                    .filter((heading) => heading.getBoundingClientRect().top < 140)
                    .pop();
                if (fallback) {
                    setActiveTocLink(links, fallback.id);
                }
            },
            {
                rootMargin: "-112px 0px -68% 0px",
                threshold: [0, 1],
            }
        );

        headings.forEach((heading) => observer.observe(heading));
        setActiveTocLink(links, headings[0].id);
    }

    function initCodeCopy() {
        document.querySelectorAll("[data-code-copy]").forEach((button) => {
            button.addEventListener("click", async () => {
                const block = button.closest(".blog-code-block");
                const code = block ? block.querySelector("code") : null;
                if (!code) {
                    return;
                }

                const originalLabel = button.getAttribute("aria-label") || "Copy code";
                const originalTitle = button.getAttribute("title") || "Copy code";
                const status = button.querySelector(".copy-status");
                try {
                    await navigator.clipboard.writeText(code.textContent || "");
                    button.setAttribute("aria-label", "Copied");
                    button.setAttribute("title", "Copied");
                    if (status) {
                        status.textContent = "Copied";
                    }
                    button.classList.add("copy-success");
                } catch (error) {
                    button.setAttribute("aria-label", "Copy failed");
                    button.setAttribute("title", "Copy failed");
                    if (status) {
                        status.textContent = "Copy failed";
                    }
                }

                window.setTimeout(() => {
                    button.setAttribute("aria-label", originalLabel);
                    button.setAttribute("title", originalTitle);
                    if (status) {
                        status.textContent = originalLabel;
                    }
                    button.classList.remove("copy-success");
                }, 1400);
            });
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        initToc();
        initCodeCopy();
    });
})();
