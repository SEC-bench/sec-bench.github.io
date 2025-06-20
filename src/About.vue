<template>
  <div class="content-wrapper">
    <div class="content-box">
      <h2 class="text-title">About</h2>
      <p class="text-content">
        SEC-Bench is the first fully automated benchmarking framework for evaluating LLM agents on authentic security engineering tasks.
        It employs a novel multi-agent scaffold that automatically constructs code repositories with harnesses,
        reproduces vulnerabilities in isolated environments, and generates gold patches for reliable evaluation.
        Read more about SEC-Bench in our <a href="https://arxiv.org/abs/2506.11791" target="_blank">paper</a>!
      </p>
      <h3 class="text-title">Citation</h3>
      If you found the <a href="https://sec-bench.github.io">SEC-bench</a> helpful for your work, please cite as follows:
      <div class="text-content">
      <pre id="citation"><code>@article{lee2025sec,
  title={SEC-bench: Automated Benchmarking of LLM Agents on Real-World Software Security Tasks},
  author={Lee, Hwiwon and Zhang, Ziqi and Lu, Hanxiao and Zhang, Lingming},
  journal={arXiv preprint arXiv:2506.11791},
  year={2025}
}</code></pre>
      <br />
      <b>Disclaimer:</b> SEC-bench is for research purposes only. Models
      evaluated on SEC-bench may produce unexpected results.
      We are not responsible for any damages caused by the use of
      SEC-bench, including but not limited to, any loss of profit, data,
      or use of data.
      <br /><br />
      <b>Acknowledgements:</b> This leaderboard is a modified version based on the <a
        href="https://multi-swe-bench.github.io">Multi-SWE-bench leaderboard</a>,
      and we are using this template according to the license of the Multi-SWE-bench dashboard template.
      We express our deepest gratitude to the creators of the Multi-SWE-bench and SWE-bench datasets.
      </div>
      <p class="text-content">
        Correspondence to: <a href="mailto:hwiwonl2@illinois.edu">hwiwonl2@illinois.edu</a>
        <br />
      </p>
      <div class="content-wrapper" style="display: flex; flex-direction: row;">
      </div>
    </div>
  </div>
</template>
