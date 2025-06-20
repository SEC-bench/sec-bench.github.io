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
        <a href="https://arxiv.org/abs/2506.11791">
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
        <router-link to="/submit">
          <button class="outline">
            <i class="fa fa-upload"></i> Submit&nbsp;
          </button>
        </router-link>
      </div>
    </div>
  </section>
</template>

<style lang="css">
.gradient-background {
  height: 400px;
  background:
    radial-gradient(circle at 20% 30%, #FF5F05, transparent 40%), /* UIUC Orange */
    radial-gradient(circle at 80% 40%, #FFA500, transparent 40%), /* Lighter Orange */
    radial-gradient(circle at 20% 70%, #D2691E, transparent 40%), /* Darker Orange */
    radial-gradient(circle at 70% 90%, #FF5F05, transparent 40%), /* UIUC Orange */
    radial-gradient(circle at 50% 50%, #FFA500, transparent 40%); /* Lighter Orange */
  background-blend-mode: screen;
  display: flex;
  align-items: center;
}
</style>

<script setup lang="ts">
</script>