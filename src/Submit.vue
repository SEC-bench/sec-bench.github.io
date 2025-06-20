<template>
  <section class="gradient-background">
    <div class="content-wrapper title-wrapper" style="flex-direction: column">
      <div style="
          display: flex;
          flex-direction: row;
          align-items: center;
          padding-bottom: 15px;
        ">
        <!--        <h1 style="font-size: 60px; margin: 0; color: black">Multi-SWE-bench</h1>-->
        <!--        <h1 style="font-size: 60px; margin: 0; color: black; border: 3px solid white; padding: 10px; border-radius: 10px; display: inline-block;">-->
        <!--    Multi-SWE-bench-->
        <!--        </h1>-->
        <h1 style="font-size: 60px; margin: 0; color: black;
    text-shadow: -2px -2px 0 white, 2px -2px 0 white, -2px 2px 0 white, 2px 2px 0 white;">
          SEC-bench
        </h1>
        <!-- <img src="/logo-v3.svg" style="height: 100px; padding-left: 0.5em" /> -->
      </div>
      <h3 style="color: #333">
        Automated Benchmarking of LLM Agents on Real-World Software Security Tasks
      </h3>
      <div class="content-wrapper header button-group" style="margin-top: 2em">

        <!-- Paper-->
        <a href="https://arxiv.org/abs/2504.02605">
          <button class="outline">
            <i class="fa fa-paperclip"></i> Paper&nbsp;
          </button>
        </a>

        <!-- Code -->
        <a href="https://github.com/SEC-bench/SEC-bench">
          <button class="outline">
            <i class="fab fa-github"></i> Code&nbsp;
          </button>
        </a>

        <!-- Data -->
        <a href="https://huggingface.co/datasets/SEC-bench/SEC-bench">
          <button class="outline">
            <i class="fa fa-database"></i> Data&nbsp;
          </button>
        </a>
        <!--       <a href="https://arxiv.org/abs/2504.02605">
          <button class="outline">
            <i class="fa fa-paperclip"></i> Paper&nbsp;
          </button>
        </a>
        <a href="https://github.com/multi-swe-bench/multi-swe-bench">
          <button class="outline">
            <i class="fab fa-github"></i> Code&nbsp;
          </button>
        </a>  -->
        <router-link to="/">
          <button class="outline">
            <i class="fa fa-upload"></i> Home&nbsp;
          </button>
        </router-link>
      </div>
    </div>
  </section>
  <section class="main-container">
    <div class="content-wrapper" style="display: flex; justify-content: center; align-items: center;">
      <div style="background-color: black; padding: 1.5em 1em; color: white; border-radius: 1em; text-align: center; width: 80%;">
        All official submissions to the SEC-bench leaderboard are maintained at
        <a target="_blank" rel="noopener noreferrer" href="https://github.com/SEC-bench/experiments/tree/main" style="color: #00ADD8;">
          <i class="fab fa-github"></i> SEC-bench/experiments
        </a>
      </div>
    </div>
    <div class="content-wrapper">
      <div class="content-box">
        <h3>
          Submit to SEC-bench Leaderboard
        </h3>
        <p>
          If you are interested in submitting your model to the <router-link to="/">SEC-bench Leaderboard</router-link>, please do the following:
        </p>
        <ol>
          <li>Fork the <a target="_blank" rel="noopener noreferrer" href="https://github.com/SEC-bench/experiments/tree/main">SEC-bench/experiments</a> repository.</li>
          <li>Clone the repository. Due to this repository's large diff history, consider using `git clone --depth 1` if cloning takes too long.</li>
          <li>Under the task that you evaluate on (e.g. <code>evaluation/Patch/</code>), create a new folder with the model name (e.g. <code>swea_o3-mini</code>).</li>
          <li>Within the folder, please include the following files:
            <ul>
              <li><code>report.jsonl</code>: A Report file that summarizes the evaluation results</li>
              <li><code>metadata.yaml</code>: Metadata for how result is shown on website. Please include the following fields:</li>
              <ul>
                <li><code>name</code>: The name of your leaderboard entry</li>
                <li><code>orgIcon</code> (optional): URL/link to an icon representing your organization</li>
                <li><code>oss</code>: <code>true</code> if your system is open-source</li>
                <li><code>site</code>: URL/link to more information about your system</li>
                <li><code>verified</code>: <code>false</code> (See below for results verification)</li>
                <li><code>date</code>: Date of submission</li>
              </ul>
              <li><code>trajs/</code>: Reasoning trace reflecting how your system solved the problem</li>
              <li><code>logs/</code>: SEC-bench evaluation artifacts dump, which stores the contents of the language folder after the evaluation </li>
<!--              <li><code>README.md</code>: Include anything you'd like to share about your model here!</li>-->
            </ul>
          </li>
<!--          <li>Run <code>python -m analysis.get_results evaluation/&lt;split&gt;/&lt;date + model&gt;</code></li>-->
          <li>Create a pull request to the `lhxxh/exp_secbench` repository with the new folder.</li>
        </ol>
        <p>
          You can refer to this <a target="_blank" rel="noopener noreferrer" href="https://github.com/SEC-bench/SEC-bench">tutorial</a> for a quick overview of how to evaluate your model on SEC-bench.
        </p>        
      </div>
    </div>
    <!--
    <div class="content-wrapper">
      <div class="content-box">
        <h3>
          Submission Guidelines
        </h3>
        <p>
          Please note that we consider an eligible submission to the Multi-SWE-bench leaderboard to satisfy these criteria:
        </p>
        <ol>
          <li>The use of the <code>hints_text</code> field is <i>not</i> allowed. See the explanation <a target="_blank" rel="noopener noreferrer" href="https://github.com/princeton-nlp/SWE-bench/issues/133">here</a>.</li>
          <li>The result should be pass@1. There should be one execution log per task instance for all task instances.</li>
          <li>The result should <i>not</i> be in the "Oracle" retrieval setting. The agent cannot be told the correct files to edit, where "correct" refers to the files modified by the reference solution patch.</li>
        </ol>
      </div>
    </div>
    -->
    
    <div class="content-wrapper">
      <div class="content-box">
        <h3>Verify Your Results</h3>
        <p>
          The <i>Verified</i> check ✓ indicates that we (the SEC-bench team) received access to the model and were able to reproduce the patch generations.
        </p>
        <p style="margin-top:0.5em;">
          If you are interested in receiving the "verified" checkmark ✓ on your submission, please do the following:
        </p>
        <ol>
          <li>Create an issue.</li>
          <li>In the issue, provide us instructions on how to run your model on SEC-bench.</li>
          <li>We will run your model on a random subset of SEC-bench and verify the results.</li>
        </ol>
      </div>
    </div>
    <!--
    <div class="content-wrapper">
      <div class="content-box" id="reasoning-traces">
        <h3>Reasoning Traces</h3>
        <p>
          (07/29/2024) We have updated the SWE-bench leaderboard submission criteria to require the inclusion of <i>reasoning traces</i>.
          The goal of this requirement is to provide the community with more insight into how cutting edge methods work without requiring a code release (although the latter is still highly encouraged!).
        </p>
        <p><b>What is a reasoning trace?</b></p>
        <p>
          A reasoning trace is a text-based file that describes the steps your system took to solve a task instance.
          It should provide a detailed account of the reasoning process that your system used to arrive at its solution.
        </p>
        <p>
          We purposely do not explicitly define reasoning traces in a strict, explicit format.
        </p>
        <p>
          We do have some guidelines. the reasoning trace should be...
          <ul>
            <li>Human-readable.</li>
            <li>Reflects the intermediate steps your system took that led to the final solution.</li>
            <li>Generated <i>with</i> the inference process, not post-hoc.</li>
          </ul>
        </p>
        <p>
          We do not require reasoning traces to be...
          <ul>
            <li>In a specific file format (e.g. <code>json</code>, <code>yaml</code>, <code>md</code>)</li>
            <li>Conform to a specific problem solving style (e.g. agentic, procedural, etc.)</li>
          </ul>
        </p>
        <p>
          A simple solution to this? When running inference, simply log the intermediate output generated by your system.
          For an example, see <a target="_blank" rel="noopener noreferrer" href="https://github.com/swe-bench/experiments/tree/main/evaluation/lite/20240402_sweagent_gpt4/logs">SWE-agent + GPT-4 Turbo Trajectories</a>.
          In short, our requirements for what a reasoning trace should specific look like are non-specific.
          We trust you to provide a detailed account of how your system solved the task instance.
        </p>
        <p><b>Why are we requiring it?</b></p>
        <p>
          We believe that reasoning traces can provide valuable insights into how cutting edge methods work without requiring a code release.
        </p>
        <p>
          As of this post (7/29/2024), we have received many submissions that have pushed the state of the art on SWE-bench, which is exciting to see!
        </p>
        <p>
          However, we have also found that the top-performing submissions to SWE-bench typically have not open sourced their code nor been verified.
          We recognize that some leaderboard participants (1) would like to add an entry to SWE-bench but (2) do not want to release their code or proprietary system, which is completely understandable.
          On the other hand, given that open source systems submitted to SWE-bench have propelled the development of closed-source participants, we would like to continuing promoting development on SWE-bench as a community-level collaborative process.
        </p>
        <p>
          Therefore, we believe that providing reasoning traces serves as a valuable compromise between these two groups.
        </p>
        <p><b>What should I submit?</b></p>
        <ol>
          <li>Create a <code>trajs/</code> folder in your submission directory.</li>
          <li>Within this folder, upload a reasoning trace per task instance that your system generated a prediction for.</li>
          <li>Make sure the naming convention of the reasoning trace file reflects the SWE-bench task instance it corresponds to. (e.g. <code>apache__dubbo-10638.md</code>)</li>
        </ol>
        <p>
          We will review the reasoning traces you submit.
          We plan to only accept submissions with reasoning traces for the SWE-bench leaderboard.
        </p>
      </div>
    </div>
    -->
  </section>
</template>

<style lang="scss" scoped>

code {
  background-color: #ddd;
  color: black;
}

h3 {
  margin-bottom: 0.5em;
}

li {
  margin-bottom: 0.5em;
}
/* Style for the entire code block */
pre {
    background-color: #f4f4f4;
    border: 1px solid #ccc;
    padding: 5px;
    font-family: "Courier New", monospace;
    font-size: 16px;
    overflow-x: auto;  /* Enables horizontal scrolling for long lines */
    white-space: pre-wrap;  /* Ensures long lines wrap properly */
    word-wrap: break-word;  /* Prevents words from overflowing */
    margin: 10px 0 10px 0;
    width:90%;
}

</style>
<script setup lang="ts">
</script>