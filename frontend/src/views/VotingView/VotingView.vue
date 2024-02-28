<script setup lang="ts">
import kirbPhone from "./kirb_phone.gif";
import kirbPhones from "./kirb_phones.png";
import interfaceCategoryGrid from "./interface-category-grid.png";
import interfaceVideoPlay from "./interface-video-play.png";
import interfaceDownArrow from "./interface-down-arrow.png";
import interfaceUpArrow from "./interface-up-arrow.png";
import interfaceBulb from "./interface-bulb.png";
import interfacePlay from "./interface-play.png";
import kirbThanks from "./kirb_thanks.png";
import kirbThink from "./kirb_think.png";
import StarWidget from "@/components/StarWidget";
import type { UserVote, VotingData } from "@/types";
import { onMounted, reactive, ref } from "vue";

const working = ref(false);
const mode = ref<null | "vote" | "thanks">(null);
const weekData = reactive<{
  data:
    | null
    | (VotingData & {
        entries: (VotingData["entries"][number] & Record<string, number>)[];
      });
}>({
  data: null,
});
const viewedEntryIndex = ref<number | null>(null);
const showEntryList = ref(false);
const pdfColorInvert = ref(false);
const numEntriesRated = ref(0);
const userVoteKey = ref(""); // TODO: Grab from AuthKey

onMounted(async () => {
  try {
    working.value = true;

    // Are we admin?
    // TODO: Separate into components

    const searchParams = new URLSearchParams(window.location.search);
    const authKey = searchParams.get("key") as string;

    let weekResponse;
    if (!authKey) {
      weekResponse = await fetch("/api/entry_data");
    } else {
      weekResponse = await fetch("/api/admin/get_preview_data/", {
        headers: {
          authorization: `Bearer: ${authKey}`,
        },
      });
    }

    if (!weekResponse.ok) {
      alert("Something went wrong: " + (await weekResponse.text()));
    } else {
      const weekDataResponse = await weekResponse.json();

      weekData.data = weekDataResponse;
      mode.value = "vote";
    }
  } finally {
    working.value = false;
  }
});

const viewEntry = function (entryIndex: number) {
  viewedEntryIndex.value = entryIndex;
  showEntryList.value = false;
};

const toggleEntryContainer = function () {
  showEntryList.value = !showEntryList.value;
};

const toggleNightMode = function () {
  pdfColorInvert.value = !pdfColorInvert.value;
};

const selectAdjacentEntry = function (offset: number) {
  if (!weekData.data) return;

  if (viewedEntryIndex.value === null) return;

  let index = viewedEntryIndex.value + offset;

  if (index < 0) {
    index = 0;
  } else if (index >= weekData.data.entries.length) {
    index = weekData.data.entries.length - 1;
  }

  viewedEntryIndex.value = index;
  showEntryList.value = false;
};

const updateNumEntriesRated = function () {
  if (!weekData.data) return;

  var total = 0;

  for (const entry of weekData.data.entries) {
    for (const param of weekData.data.voteParams) {
      if (entry[param] != null && entry[param] != 0) {
        total++;
        break;
      }
    }
  }

  numEntriesRated.value = total;
};

const submitVote = async function () {
  if (!weekData.data) {
    return;
  }
  try {
    working.value = true;

    if (userVoteKey.value == "") {
      alert(
        'Please enter a vote key! (To obtain a vote key, DM the command "vote!vote" to @8Bot on the 8BMT discord server.',
      );
      return;
    }

    const voteData = {
      votes: [] as UserVote[],
      voteKey: userVoteKey.value,
    };

    for (const entry of weekData.data.entries) {
      for (const param of weekData.data.voteParams) {
        if (entry[param] != null) {
          const newData = {
            entryUUID: entry.uuid,
            voteForName: entry.entrantName,
            voteParam: param,
            rating: entry[param],
          };
          voteData.votes.push(newData);
        }
      }
    }

    const response = await fetch("/api/submit_vote", {
      method: "POST",
      body: JSON.stringify(voteData),
      headers: {
        authorization: `Bearer: ${userVoteKey.value}`,
      },
    });
    if (!response.ok) {
      throw new Error("...");
    }

    mode.value = "thanks";
  } catch (e) {
    alert("Something went wrong :/\nMake sure you entered a valid vote key");
  } finally {
    working.value = false;
  }
};

// TODO: CSS
const truncateString = function (s: string, length: number) {
  if (s.length > length) {
    return s.slice(0, length - 1) + "...";
  }
  return s;
};
</script>

<template>
  <div v-if="mode === null || weekData.data === null">Loading...</div>
  <div v-else-if="mode === 'vote'">
    <div v-show="working">
      <div class="progress-img">
        <img :src="kirbPhone" />
        <p>I'm taking good care of things, hold on!</p>
      </div>
    </div>
    <transition name="entry-list-toggle">
      <div class="entries-container" v-show="showEntryList">
        <h2 class="week-title">{{ weekData.data.theme }}</h2>
        <h3 class="week-subtitle">
          {{ weekData.data.date }} - {{ weekData.data.entries.length }} entries
        </h3>
        <table cellpadding="0" class="entry-table">
          <tr class="entry-table-header-row">
            <th class="entry-table-header">Entrant</th>
            <th class="entry-table-header">Composition Title</th>
            <th class="entry-table-header">View & Listen</th>
            <th class="entry-table-header">Download</th>
            <th class="entry-table-header">Use Of Prompt Theme</th>
            <th class="entry-table-header">Score Quality</th>
            <th class="entry-table-header">Overall Rating</th>
          </tr>
          <tr
            v-for="(entry, entryIndex) in weekData.data.entries"
            :key="entry.uuid"
          >
            <td class="entry-cell">{{ entry.entrantName }}</td>
            <td class="entry-cell">{{ entry.entryName }}</td>
            <td
              class="entry-cell"
              :class="{
                'entry-cell-selected': viewedEntryIndex == entryIndex,
              }"
            >
              <button class="icon-button" @click="viewEntry(entryIndex)">
                <img :src="interfaceVideoPlay" alt="Play" />
              </button>
            </td>
            <td class="entry-cell">
              <a
                :href="entry.mp3Url ?? undefined"
                target="_blank"
                style="font-size: 0.7em"
                >MP3</a
              >
              <a
                :href="entry.pdfUrl ?? undefined"
                target="_blank"
                style="font-size: 0.7em"
                >PDF</a
              >
            </td>
            <td
              class="entry-cell"
              v-for="voteParam in weekData.data.voteParams"
              :key="voteParam"
              style="margin: auto; width: 6em"
            >
              <StarWidget
                :helptipdefs="weekData.data.helpTipDefs[voteParam]"
                v-model="weekData.data.entries[entryIndex][voteParam]"
                @update:modelValue="updateNumEntriesRated"
              />
            </td>
          </tr>
        </table>
        <div class="vote-submit-area" v-if="weekData.data.votingOpen">
          <p>
            You've rated {{ numEntriesRated }}/{{
              weekData.data.entries.length
            }}
            entries.
          </p>
          <input
            v-model="userVoteKey"
            placeholder="Paste your vote token here"
          />
          <button @click="submitVote()" class="text-button">Submit Vote</button>
          <br />
          <p style="font-size: 0.8em">
            DM @8Bot the command "vote!vote" to obtain a vote token.
          </p>
          <p>
            <a
              href="https://github.com/wilm0x42/wVote/wiki/Voting-System-Details#how-scores-are-determined"
              target="_blank"
              rel="noopener noreferrer"
              >How does the voting system work?</a
            >
          </p>
        </div>
        <div class="vote-submit-area" v-else>
          <p>Voting for this week is now closed.</p>
        </div>
      </div>
    </transition>

    <div
      class="pdf-container"
      :class="{
        'pdf-container-full': !showEntryList,
        'pdf-container-small': showEntryList,
      }"
    >
      <div
        v-if="viewedEntryIndex === null"
        id="pdf-viewer"
        class="pdf-viewer-welcome"
      >
        <div id="pdf-alt" class="pdf-alt">
          <img width="150px" :src="kirbPhones" />
          <h2>
            Welcome!<br />Select one of the entries on the left to view its
            score.
          </h2>
        </div>
      </div>
      <object
        v-else
        id="pdf-viewer"
        class="pdf-viewer-live"
        :class="{ 'pdf-color-invert': pdfColorInvert }"
        :data="weekData.data.entries[viewedEntryIndex].pdfUrl ?? undefined"
        type="application/pdf"
      >
        <div id="pdf-alt" class="pdf-alt">
          <img width="150px" :src="kirbThink" />
          <h2>
            <a
              :href="
                weekData.data.entries[viewedEntryIndex].pdfUrl ?? undefined
              "
              >Link to PDF (embedded viewer failed)</a
            >
          </h2>
        </div>
      </object>
    </div>

    <table cellpadding="0" class="viewer-control-bar">
      <td width="48px" class="viewer-control">
        <button class="icon-button" @click="toggleEntryContainer()">
          <img :src="interfaceCategoryGrid" />
        </button>
      </td>
      <td width="48px" class="viewer-control">
        <button class="icon-button" @click="selectAdjacentEntry(-1)">
          <img :src="interfaceUpArrow" />
        </button>
      </td>
      <td width="48px" class="viewer-control">
        <button class="icon-button" @click="selectAdjacentEntry(1)">
          <img :src="interfaceDownArrow" />
        </button>
      </td>
      <td
        v-if="viewedEntryIndex != null"
        class="viewer-control"
        style="text-align: center"
        width="400px"
      >
        <!-- // TODO: CSS -->
        <p>
          {{
            truncateString(
              `${weekData.data.entries[viewedEntryIndex].entrantName} - ${weekData.data.entries[viewedEntryIndex].entryName}`,
              60,
            )
          }}
        </p>

        <p></p>
      </td>
      <td
        v-if="viewedEntryIndex != null"
        class="viewer-control"
        style="width: 250px"
      >
        <div v-if="weekData.data.entries[viewedEntryIndex].mp3Format == 'mp3'">
          <audio
            controls
            :src="weekData.data.entries[viewedEntryIndex].mp3Url ?? undefined"
            type="audio/mpeg"
          ></audio>
        </div>
        <div v-else>
          <img :src="interfacePlay" />
          <a
            :href="weekData.data.entries[viewedEntryIndex].mp3Url ?? undefined"
            target="_blank"
            style="position: relative; top: -12px"
            >Listen Here!</a
          >
        </div>
      </td>
      <td
        v-if="viewedEntryIndex != null"
        class="vote-stars-bottom-panel"
        style="width: 320px"
      >
        <table cellpadding="0" class="current-stars">
          <tr>
            <td
              class="entry-cell"
              style="padding: 2px"
              v-for="voteParam in weekData.data.voteParams"
              :key="voteParam"
            >
              <p class="vote-star-bottom-label">{{ voteParam }}</p>
              <StarWidget
                v-model="weekData.data.entries[viewedEntryIndex][voteParam]"
                :helptipdefs="weekData.data.helpTipDefs[voteParam]"
                @update:modelValue="updateNumEntriesRated"
              >
              </StarWidget>
            </td>
          </tr>
        </table>
      </td>
      <td>
        <!-- empty cell to expand and fill space -->
      </td>
      <td width="48px" class="viewer-control">
        <button class="icon-button" @click="toggleNightMode()">
          <img :src="interfaceBulb" />
        </button>
      </td>
    </table>
  </div>
  <div v-else-if="mode === 'thanks'">
    <div id="content">
      <div class="submit-babble">
        <h2>Thank you for voting!</h2>
        <p>Your vote has been recorded. I will guard it with my life. :)</p>
        <img width="500px" :src="kirbThanks" />
      </div>
    </div>
  </div>
</template>
