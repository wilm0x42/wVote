<script setup lang="ts">
import kirbPhone from "./kirb_phone.gif";
import Entry from "@/components/AdminEntryEditor.vue";
import type { ThisWeek, NextWeek, Vote, AdminData } from "@/types";
import { onMounted, reactive, ref } from "vue";

const searchParams = new URLSearchParams(window.location.search);
const authKey = searchParams.get("key") as string;
const votes = ref<null | Vote[]>(null);
const weeks = ref<null | [ThisWeek, NextWeek]>(null);
const working = ref(false);

const submissionsOpen = ref(false);
const votingOpen = ref(false);
const confirmArchive = ref(null);

const spoofedEntry = reactive({
  entrantName: "Wiglaf",
  discordId: "",
  placeInCurrentWeek: false,
});

const save = async () => {
  try {
    working.value = true;
    if (!weeks.value) {
      return;
    }

    const saveData = {
      weeks: [
        {
          theme: weeks.value[0].theme,
          date: weeks.value[0].date,
          votingOpen: weeks.value[0].votingOpen,
        },
        {
          theme: weeks.value[1].theme,
          date: weeks.value[1].date,
          submissionsOpen: weeks.value[1].submissionsOpen,
        },
      ],
    };

    // TODO: Remove key from URL
    await fetch("/api/admin/edit", {
      method: "POST",
      body: JSON.stringify(saveData),
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${authKey}`,
      },
    });

    await updateWeeks();
  } finally {
    working.value = false;
  }
};

const archive = async () => {
  try {
    working.value = true;

    // TODO: Remove key from URL
    const req = await fetch("/api/admin/archive", {
      method: "POST",
      headers: {
        authorization: `Bearer ${authKey}`,
      },
    });

    if (!req.ok) {
      alert("Something went wrong: " + (await req.text()));
    } else {
      await updateWeeks();
    }
  } finally {
    working.value = false;
  }
};

const spoof = async () => {
  try {
    working.value = true;

    const saveData = {
      entrantName: spoofedEntry.entrantName,
      discordId: spoofedEntry.discordId,
      nextWeek: !spoofedEntry.placeInCurrentWeek,
    };

    const req = await fetch("/api/admin/spoof", {
      method: "POST",
      body: JSON.stringify(saveData),
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${authKey}`,
      },
    });

    if (!req.ok) {
      alert("Something went wrong: " + (await req.text()));
    } else {
      Object.assign(spoofedEntry, {
        entrantName: "Wiglaf",
        discordId: "",
        placeInCurrentWeek: false,
      });

      await updateWeeks();
    }
  } finally {
    working.value = false;
  }
};

const updateWeeks = async () => {
  const req = await fetch("/api/admin/get_admin_data", {
    headers: {
      authorization: `Bearer ${authKey}`,
    },
  });

  if (!req.ok) {
    alert("Something went wrong: " + (await req.text()));
    return;
  }

  const result: AdminData = await req.json();
  votes.value = result.votes;
  weeks.value = result.weeks;

  votingOpen.value = weeks.value[0].votingOpen;
  submissionsOpen.value = weeks.value[1].submissionsOpen;

  // TODO: Remove and use components
  const submissionsElt = document.getElementById(
    "submissions",
  ) as HTMLIFrameElement;
  submissionsElt.contentWindow?.location.reload();
};

const deleteVote = async (vote: Vote) => {
  const confirmation = window.confirm(
    "Are you sure you want to delete " +
      vote.userName +
      "'s vote? This cannot be undone.",
  );

  if (!confirmation) {
    return;
  }

  const request = await fetch("/api/admin/delete_vote/" + "/" + vote.userID, {
    method: "POST",
    headers: {
      authorization: `Bearer ${authKey}`,
    },
  });

  if (!request.ok) {
    alert("Something went wrong: " + (await request.text()));
  } else {
    await updateWeeks();
  }
};

onMounted(async () => {
  try {
    working.value = true;
    await updateWeeks();
  } finally {
    working.value = false;
  }
});
</script>

<template>
  <div id="content">
    <div v-if="votes === null || weeks === null">Loading...</div>
    <div v-else>
      <div class="submit-babble">
        <p>Welcome to the super-ugly administration interface!</p>
        <p>
          For instructions on how to use this,
          <a href="https://github.com/wilm0x42/wVote/wiki/Admin-Guide"
            >check out our barely-adequate wiki.</a
          >
        </p>
        <p>
          If you need help, or if something seems amiss, message @wilm0x42, and
          he'll ii V us back to I.
        </p>
      </div>
      <div class="admin-progress-img" v-show="working">
        <img class="admin-progress-img" :src="kirbPhone" />
      </div>
      <div class="admin-controls">
        <!-- TODO: Style -->
        <div id="weeks">
          <p>
            <label
              >Theme/title of current week
              <input
                class="admin-week-text-param"
                type="text"
                v-model="weeks[0].theme"
            /></label>
          </p>
          <p>
            <label
              >Date of current week
              <input
                class="admin-week-text-param"
                type="text"
                v-model="weeks[0].date"
            /></label>
          </p>
          <p>Voting is currently {{ votingOpen ? "OPEN" : "CLOSED" }}</p>
          <p>
            <label>Voting Open:</label>
            <label
              ><input
                type="radio"
                name="votingOpen"
                v-model="weeks[0].votingOpen"
                :value="true"
              />
              Yes</label
            >
            <label
              ><input
                type="radio"
                name="votingOpen"
                v-model="weeks[0].votingOpen"
                :value="false"
              />
              No</label
            >
          </p>

          <hr />

          <p>
            <label
              >Theme/title of next week
              <input
                class="admin-week-text-param"
                type="text"
                v-model="weeks[1].theme"
            /></label>
          </p>
          <p>
            <label
              >Date of next week
              <input
                class="admin-week-text-param"
                type="text"
                v-model="weeks[1].date"
            /></label>
          </p>
          <p>
            Submissions are currently {{ submissionsOpen ? "OPEN" : "CLOSED" }}
          </p>
          <p>
            <label>Submissions Open:</label>
            <label
              ><input
                type="radio"
                name="submissionsOpen"
                v-model="weeks[1].submissionsOpen"
                :value="true"
              />
              Yes</label
            >
            <label
              ><input
                type="radio"
                name="submissionsOpen"
                v-model="weeks[1].submissionsOpen"
                :value="false"
              />
              No</label
            >
          </p>

          <hr />

          <p>
            <button @click="save">Save changes</button>
          </p>

          <hr />

          <p>
            <label
              >Archive current week, and make next week current
              <input type="checkbox" v-model="confirmArchive"
            /></label>
            <button @click="archive" :disabled="!confirmArchive">
              Archive
            </button>
          </p>
        </div>

        <div id="createEntry">
          <p>
            <label for="newEntryEntrant">Spoofed entrant name</label
            ><input
              type="text"
              name="newEntryEntrant"
              v-model="spoofedEntry.entrantName"
            />
          </p>
          <p>
            <label for="newEntryDiscordID"
              >(Optional) Spoofed entrant discord ID</label
            ><input
              type="text"
              name="newEntryDiscordID"
              v-model="spoofedEntry.discordId"
            />
          </p>
          <p>
            <label for="newEntryWeek"
              >Place entry in current week instead of next week?</label
            ><input
              type="checkbox"
              name="newEntryWeek"
              v-model="spoofedEntry.placeInCurrentWeek"
            />
          </p>
          <p><button type="submit" @click="spoof">Spoof</button></p>
        </div>
      </div>

      <iframe
        :src="'/admin/preview/'"
        class="entries-preview"
        id="submissions"
      ></iframe>
      <!-- TODO: -->
      <!-- // <AdminPreview .../> -->

      <div class="entry-list">
        <div>
          <Entry
            v-for="entry in weeks[1].entries"
            :key="entry.uuid"
            :entry="entry"
            :next-week="true"
            :auth-key="authKey"
            @editedentry="updateWeeks"
          />
        </div>
        <div>
          <Entry
            v-for="entry in weeks[0].entries"
            :key="entry.uuid"
            :entry="entry"
            :next-week="false"
            :auth-key="authKey"
            @editedentry="updateWeeks"
          />
        </div>
      </div>

      <div class="vote-list">
        <div v-for="vote in votes" :key="vote.userID" class="vote-data">
          <a :href="'/admin/viewvote/' + '/' + vote.userID.toString()"
            >Vote from {{ vote.userName }}</a
          >
          <button @click="deleteVote(vote)">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
label {
  margin: 8px;
}

input {
  font-size: 1em;
}

h3 {
  padding: 0px;
  margin: 0px;
  font-size: 1em;
  text-decoration: underline;
  text-align: left;
}

h3:hover {
  cursor: pointer;
}

hr {
  color: #361536;
}

.admin-week-text-param {
  width: 400px;
}

.admin-entry-form {
  background: linear-gradient(
    to bottom left,
    rgba(141, 80, 141, 1),
    rgba(141, 80, 141, 0.5)
  );
  width: 500px;
  border: 1px solid black;
}

.admin-entry-param {
  text-align: center;
}

.admin-submit-form {
  margin: auto;
  width: 500px;
}

.admin-submit-button {
  background-color: white;
  box-shadow: 0px 3px 5px rgba(0, 0, 0, 0.5);
  border: 1px solid black;
  padding: 8px;
  width: 150px;
  margin-left: 175px;
}

.admin-submit-button:hover {
  cursor: pointer;
}

.submit-babble {
  text-align: center;
}

.entry-list {
  float: right;
}

.form-invalid {
  background: rgb(255, 100, 100);
}

.admin-controls {
  text-align: center;
  padding: 32px;
  border: 1px solid black;
  background: rgba(141, 80, 141, 0.5);
}

.entries-preview {
  width: 90vw;
  height: 90vh;
}

.vote-data {
  background: linear-gradient(
    to bottom left,
    rgba(141, 80, 141, 1),
    rgba(141, 80, 141, 0.5)
  );
  width: 500px;
  border: 1px solid black;
}

.admin-progress-img {
  width: 200px;
  margin: auto;
}
</style>
