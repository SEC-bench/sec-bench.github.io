<template>
  <Header></Header>
  <section class="main-container">
    <!-- <div class="content-wrapper" style="margin-top: 1em; display: flex; justify-content: center; align-items: center;">
        <button
            @click="switchLeaderboard('Full')"
          class="outline teaser swebv"
          style="flex-direction: row; display: flex; justify-content: center; align-items: center; width: 15em;">
          <img
            src="../img/logo-v3.svg"
            style="height: 1.3em; margin-right: 0.4em; margin-bottom: 0.1em;" />
            Multi-SWE-bench&nbsp;
        </button>
        <button
            @click="switchLeaderboard('Lite')"
          class="outline teaser swebl"
          style="flex-direction: row; display: flex; justify-content: center; align-items: center; width: 15em;">
          <img
            src="../img/logo-v3.svg"
            style="height: 1.3em; margin-right: 0.4em; margin-bottom: 0.1em; background-color: var(--dark_accent_color);" />
            Multi-SWE-bench mini&nbsp;
        </button>
      <button
            onclick="window.location.href = 'https://www.swebench.com';"
          class="outline teaser sweble"
          style="flex-direction: row; display: flex; justify-content: center; align-items: center; width: 10em;">
          <img
            src="../img/swellama.png"
            style="height: 1.3em; margin-right: 0.4em; margin-bottom: 0.1em;" />
            SWE-bench&nbsp;
        </button>
    </div> -->
    <div class="content-wrapper">
      <div class="content-box" v-if="tabData && tabData.length > 0">
        <h2 class="text-title">{{ LeaderboardName }}</h2>
        <ul class="tab">
          <li
            v-for="tab in tabData"
            :key="tab.tabName"
            :class="{ active: activeTab === tab.tabName }"
            @click="activeTab = tab.tabName">
            <button>{{ tab.displayName }}</button>
          </li>
        </ul>
        <div class="tabcontent tabcontentall block" v-if="filteredAndSortedResults && filteredAndSortedResults.length > 0">
          <table class="scrollable">
            <thead>
              <tr>
                <th><div class="sticky-header-content">Model</div></th>
                <th>
                  <div class="sticky-header-content" @click="sortColumn('overall')">
                    % Resolved
                    <span :class="getSortIconClass('overall')" style="font-size: 14px;">▼</span>
                  </div>
                </th>
                <th><div class="sticky-header-content">Org</div></th>
<!--                <th><div class="sticky-header-content">Date</div></th>-->
                <th><div class="sticky-header-content" @click="sortColumn('date')">Date<span :class="getSortIconClass('date')" style="margin-left: 2px;font-size: 14px;">▼</span></div></th>
                <th><div class="sticky-header-content">Logs</div></th>
                <th><div class="sticky-header-content">Trajs</div></th>
                <th><div class="sticky-header-content">Site</div></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) of filteredAndSortedResults" :key="item.name + index"> 
                <td>
                  <template v-if="index === 0">🥇 </template>
                  <template v-else-if="index === 1">🥈 </template>
                  <template v-else-if="index === 2">🥉 </template>
                  <template v-if="item.oss">🤠 </template>
                  <template v-if="item.verified">✅ </template>
                  {{ item.name }}
                </td>
                <td class="font-bold">
                  <div class="resolution-values">
                    <span>{{ (item.resolvedRate * 100).toFixed(2) }}</span>
                  </div>
                </td>
                <td class="text-center">
                  <template v-if="item.orgIcon">
                    <img :src="item.orgIcon" style="height: 1.25em;">
                  </template>
                  <template v-else> - </template>
                </td>
                <td>
                  <template v-if="item.date">
                  <span class="label-date">{{ item.date }}</span>
                  </template>
                  <template v-else> - </template>
                </td>
                <td class="text-center">
                  <template v-if="item.hasLogs">
                    <a target="_blank" rel="noopener noreferrer" :href="`${GITHUB_URL}/${item.path}/logs`">🔗</a>
                  </template>
                  <template v-else> - </template>
                </td>
                <td class="text-center">
                  <template v-if="item.hasTrajs">
                    <a target="_blank" rel="noopener noreferrer" :href="`${GITHUB_URL}/${item.path}/trajs`">🔗</a>
                  </template>
                  <template v-else> - </template>
                </td>
                <td class="text-center">
                  <template v-if="item.site">
                    <a target="_blank" rel="noopener noreferrer" :href="item.site">🔗</a>
                  </template>
                  <template v-else> - </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else>
           <p class="text-content" v-if="activeTab">Loading data for {{ activeTab }} or no models found...</p>
        </div>

        <p class="text-content">
          <span v-if="currentMode === 'Full'"> 
            <!-- This text might need to be updated or made dynamic based on the new tab structure -->
            - <span style="color:var(--dark_accent_color);"><b>% Resolved</b></span> denotes the proportion of successfully solved instances per tasks.
            <br>
          </span>
          <span v-else>
            <!-- This text might need to be updated or made dynamic -->
            - <span style="color:var(--dark_accent_color);"><b>% Resolved</b></span> denotes the proportion of successfully solved instances per tasks.
            <br>
          </span>
          - <span style="color:var(--dark_accent_color);"><b>✅ Checked</b></span> indicates that we, the SEC-bench team, received access to the system and
          were able to reproduce the artifacts of each task.
          <br>
          - <span style="color:var(--dark_accent_color);"><b>🤠 Open</b></span> refers to submissions that have open-source code. This does <i>not</i> necessarily mean the underlying model is open-source.
          <br>
          <br>

          If you'd like to submit to the leaderboard, please check <router-link to="/submit">this page</router-link>.
        </p>
      </div>
      <div v-else>
        <p class="text-content">Loading leaderboard data or no data available...</p>
      </div>
    </div>
    <!-- <Resources></Resources> -->
    <About></About>
  </section>
</template>

<script lang="ts" setup>

import { useLeaderboard,useVisualLeaderboard,useAllLeaderboard } from './utils'
import About from './About.vue'
import Header from './Header.vue'
// import Resources from './Resources.vue' // Assuming Resources is not used for now

// const { leaderboard, languageData, datasetResults, language, dataset, total } = useLeaderboard()
// const { visual_leaderboard, visual_languageData, visual_datasetResults, visual_language, visual_dataset, visual_total } = useVisualLeaderboard()
const { tabData, loadData } = useAllLeaderboard()

let GITHUB_URL = 'https://github.com/multi-swe-bench/experiments/tree/main/evaluation' // This might need to be dynamic if different tabs have different base URLs
let LeaderboardName = 'Leaderboard' // Can be made dynamic or come from tabData if needed

const currentMode = ref<'Full' | 'Lite'>('Full') // This might be less relevant if data isn't mode-switched in the same way
const activeTab = ref<string>('') // Will store the tabName of the active tab

// Initialize activeTab when tabData is loaded
watch(tabData, (newTabs) => {
  if (newTabs && newTabs.length > 0 && !activeTab.value) {
    activeTab.value = newTabs[0].tabName;
  }
}, { immediate: true });

async function switchLeaderboard(mode: 'Full' | 'Lite') {
  if (mode === currentMode.value) return
  currentMode.value = mode
  // loadData(); // loadData in useAllLeaderboard doesn't take mode anymore, adjust if mode switching is still needed
  // GITHUB_URL = urls[mode] // urls and leadnames might need rethinking if not tied to Full/Lite modes directly
  // LeaderboardName = leadnames[mode]
  console.warn("switchLeaderboard function may need to be adapted or removed based on new data structure if Full/Lite mode switching logic changes.")
}

// console.log({ allLeaderboards, selectedCategory, leaderboard, languageData, datasetResults, language, dataset, total}); // Old log
import { ref,computed, watch } from 'vue';

const sortOrder = ref({
  overall: 'desc',
  date: 'desc',
});

const getSortIconClass = (category: string) => {
  return {
    'sort-icon': true,
    'asc': sortOrder.value[category] === 'asc',
    'desc': sortOrder.value[category] === 'desc',
    'selected': selectedSortCategory.value === category
  };
};

const selectedSortCategory = ref('overall');

const filteredAndSortedResults = computed(() => {
  if (!tabData.value || tabData.value.length === 0 || !activeTab.value) {
    return [];
  }

  const currentTabData = tabData.value.find(tab => tab.tabName === activeTab.value);
  if (!currentTabData || !Array.isArray(currentTabData.models) || currentTabData.models.length === 0) {
    return [];
  }

  let resultsToDisplay = [...currentTabData.models];

  const keyMap = {
    overall: 'resolvedRate', // Ensure your models in JSON have 'resolvedRate'
    date: 'date',
  };

  const sortKey = keyMap[selectedSortCategory.value];
  const order = sortOrder.value[selectedSortCategory.value];

  if (!sortKey) return resultsToDisplay; // Should not happen if selectedSortCategory is always valid

  return resultsToDisplay.sort((a, b) => {
    if (sortKey === 'date') {
      // Ensure date is a comparable format, e.g., string 'YYYY-MM-DD' or Date object
      return order === 'asc'
        ? new Date(a.date).getTime() - new Date(b.date).getTime()
        : new Date(b.date).getTime() - new Date(a.date).getTime();
    }
    // For other keys, assume numeric comparison
    return order === 'asc' ? a[sortKey] - b[sortKey] : b[sortKey] - a[sortKey];
  });
});

function sortColumn(category: string) {
    if (selectedSortCategory.value === category) {
    sortOrder.value[category] = sortOrder.value[category] === 'desc' ? 'asc' : 'desc';
  } else {
    selectedSortCategory.value = category;
    // Optionally reset to desc when changing column, or keep current order if that makes sense
    // sortOrder.value[category] = 'desc'; 
  }
}

</script>

<style lang="scss">
.resolution-subcategories {
  display: flex;
  justify-content: space-between;
  font-size: 0.85em;
  margin-top: 0.3em;
  color: #666;
  font-weight: normal;
}

.resolution-subcategories span {
  font-weight: bold;
  flex: 1;
  text-align: center;
  padding: 0 0.2em;
}

.resolution-values {
  display: flex;
  justify-content: space-between;
}

.resolution-values span {
  flex: 1;
  text-align: center;
  padding: 0 0.2em;
}

ul.tab {
  list-style-type: none;
  margin: 0 0 1em 0;      // Add some bottom margin for separation
  padding: 0;
  overflow: hidden;
  border-bottom: 2px solid #ddd; // Separator line for the tab bar
}

ul.tab li {
  float: left;
  margin-right: 5px;      // Space between tabs
}

ul.tab li button {
  border: 1px solid #ddd; 
  border-bottom: none;      // ul.tab provides the bottom line for the active tab area
  border-radius: 6px 6px 0 0; // Rounded top corners for tab look
  color: var(--accent_color);   // Use accent color for text on inactive tabs
  background-color: #f0f0f0; // Light gray background for inactive tabs
  display: inline-block;
  font-size: 16px;
  padding: 10px 20px;       // Adjusted padding for a more substantial feel
  text-align: center;
  text-decoration: none;
  transition: background-color 0.3s, color 0.3s, border-color 0.3s;
  font-weight: 500;         // Medium font weight for readability
  cursor: pointer;
}

ul.tab li button:hover {
  background-color: #e0e0e0; // Slightly darker on hover for inactive tabs
  color: var(--dark_accent_color, var(--accent_color)); // Darken text, fallback to accent_color
}

ul.tab li.active button {
  background-color: var(--accent_color); // Prominent background for active tab
  color: white;                   // White text for active tab
  border-color: var(--accent_color); // Border matches background
  font-weight: bold;              // Bold text for active tab
  // The bottom border of the ul.tab will make it look like the active tab is connected
}

// Remove or comment out old .tab-item if it's no longer used after these changes to ul.tab
/*
.tab-item {
  font-weight: bold;
  cursor: pointer;
  height: 16px;
  padding: 8px 12px;
  border-bottom: 2px solid var(--accent_color);
  transition: all 0.3s ease;

  &.active {
    background-color: var(--accent_color);
    color: white;
    cursor: default;
  }
}
*/

ul.tab li.disabled { // Keep disabled style if still relevant
  pointer-events: none;
  opacity: 0.5;
}

.sort-icon {
  color: gray;
  margin-left: -2px;
  transition: transform 0.3s ease; 
  display: inline-block;
}

.sort-icon.asc {
  transform: rotate(180deg);
}

.sort-icon.desc {
  transform: rotate(0deg); 
}

.sort-icon.selected {
  color: #14c659; 
  font-weight: bold;
}

button {
  cursor: pointer;
  outline: none;

  &.outline {
    font-size: 16pt;
    height: 2em;
    width: 7em;
    position: relative;
    background: transparent;
    border: 0px;
    border-radius: 0.5em;
    padding: 0em 0em;
    margin: 0.2em 0.5em;
    transition: background-color 0.1s linear, color 0.1s linear;
    color: var(--accent_color);
    background-color: white;

    &.multimodal {
      color: var(--slate_gray);
    }

    &.teaser {
      border: 1px solid transparent; /* Specify border style */
      border-radius: 0.5em;
      transition: box-shadow 1s ease, border-color 1s ease;
      box-shadow: 0px 4px 10px rgba(0, 123, 255, 0.3);
    }
  }

  &.outline:hover {
    color: wheat;
    border-color: wheat;
  }

  &.outline.teaser.swebm {
    background-color: var(--slate_gray);
    color: white;
  }

  &.outline.teaser.swebm:hover {
    color: var(--slate_gray);
    background: radial-gradient(circle at 10% 30%, rgba(255, 99, 71, 1), transparent 40%),
    radial-gradient(circle at 30% 70%, rgba(0, 255, 127, 1), transparent 40%),
    radial-gradient(circle at 50% 30%, rgba(70, 130, 180, 1), transparent 40%),
    radial-gradient(circle at 70% 70%, rgba(255, 165, 0, 1), transparent 40%),
    radial-gradient(circle at 80% 30%, rgba(138, 43, 226, 1), transparent 40%);
    transform: scale(1.05);
  }

  &.outline.teaser.swebv {
    background-color: #d1a22b;
    color: white;
  }

  &.outline.teaser.swebv:hover {
    background: linear-gradient(to right, rgb(209, 162, 43), rgb(209, 162, 43), rgb(209, 162, 43));
    transform: scale(1.05);
  }
//#93cd7c
  // 5DAEECFF
  &.outline.teaser.swebl {
    background-color: var(--dark_accent_color);
    color: white;
  }

  &.outline.teaser.swebl:hover {
    transform: scale(1.05);
  }

  &.outline.teaser.sweble {
    background-color: #1696e1;
    color: white;
  }

  &.outline.teaser.sweble:hover {
    transform: scale(1.05);
  }
}
</style>
