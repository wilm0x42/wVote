<script setup lang="ts">
import { ref, onMounted } from "vue";

type Entry = {
  uuid: string;
  entryName: string;
  entrantName: string;
  mp3Url: string;
  pdfUrl: string;
  mp3Format: "mp3" | "external" | null;
};

const mode = ref<null | "submit" | "thanks">(null);
const working = ref(false);
const authKey = ref("");
const pdfFormat = ref<"keep" | "upload">("upload");
const mp3Format = ref<"keep" | "upload" | "external">("upload");
const validHosts = ref([]);
const mp3File = ref<null | {
  fileName: string;
  file: File;
}>(null);
const mp3Link = ref("");
const pdfFile = ref<null | {
  fileName: string;
  file: File;
}>(null);
const entry = ref<Entry | null>(null);

const submit = async () => {
  try {
    if (mode.value !== "submit" || !entry.value) {
      throw new Error("Invalid state");
    }
    working.value = true;

    const formData = new FormData();
    if (entry.value.entryName.length < 1) {
      throw new Error("Please enter a name");
    }
    formData.append("entryName", entry.value.entryName);
    if (pdfFormat.value === "upload") {
      if (!pdfFile.value) {
        throw new Error(
          "You've chosen to upload a PDF but haven't picked one.",
        );
      }
      formData.append("pdf", pdfFile.value.file, pdfFile.value.fileName);
    }
    if (mp3Format.value === "external") {
      formData.append("mp3Link", mp3Link.value);
    } else if (mp3Format.value === "upload") {
      if (!mp3File.value) {
        throw new Error(
          "You've chosen to upload am MP3 but haven't picked one.",
        );
      }
      formData.append("mp3", mp3File.value.file, mp3File.value.fileName);
    }
    const request = await fetch(
      `/api/edit/post/${entry.value.uuid}/${authKey.value}`,
      {
        method: "POST",
        body: formData,
      },
    );
    if (!request.ok) {
      throw new Error("Something went wrong: " + (await request.text()));
    }
    mode.value = "thanks";
  } catch (e) {
    alert((e as Error).toString());
  } finally {
    working.value = false;
  }
};

const setFile = (type: "mp3" | "pdf", event: Event) => {
  if (!event.target) {
    return;
  }
  if (!(event.target instanceof HTMLInputElement)) {
    return;
  }
  if (!event.target.files) {
    return;
  }

  const file = event.target.files[0];
  if (type === "mp3") {
    mp3File.value = {
      fileName: file.name,
      file,
    };
  }

  if (type === "pdf") {
    pdfFile.value = {
      fileName: file.name,
      file,
    };
  }
};

const mp3LinkError = () => {
  if (mp3Link.value === "" || mp3Link.value === null) {
    return "Link can't be empty.";
  }

  for (const host of validHosts.value) {
    if (mp3Link.value.startsWith(host)) {
      return false;
    }
  }

  return (
    "This audio hosting website is not in the approved list. Please use any of these: " +
    validHosts.value.join(", ") +
    "."
  );
};

onMounted(async () => {
  mode.value = "submit";
  working.value = true;
  try {
    const hostsRequest = await fetch("/api/allowed_hosts");
    if (!hostsRequest.ok) {
      throw new Error(
        "Something went wrong: " +
          (await hostsRequest.text()) +
          " - Try refreshing the page or notify the admins in Discord",
      );
    }

    validHosts.value = await hostsRequest.json();

    const searchParams = new URLSearchParams(window.location.search);
    authKey.value = searchParams.get("key")!;

    const request = await fetch("/api/entry_data/" + authKey.value);

    if (!request.ok) {
      throw new Error("Something went wrong: " + (await request.text()));
    }

    const entryData: Entry = await request.json();

    if (entryData.mp3Format !== "mp3") {
      // If it's a link, populate the field
      mp3Link.value = entryData.mp3Url;
    }

    if (entryData.mp3Url) {
      mp3Format.value = "keep";
    }

    if (entryData.pdfUrl) {
      pdfFormat.value = "keep";
    }
    mode.value = "submit";
    entry.value = entryData;
  } catch (e) {
    alert((e as Error).toString());
  } finally {
    working.value = false;
  }
});
</script>

<template>
  <div v-if="mode === null">Loading...</div>
  <div v-else-if="mode === 'submit' && entry">
    <div v-if="working" class="progress-img">
      <img class="progress-img" src="../static/kirb_phone.gif" />
      <p>I'm taking good care of things, hold on!</p>
    </div>
    <div v-else>
      <div class="submit-babble">
        <h2>Hello, {{ entry.entrantName }}!</h2>
        <p>
          Thanks for participating this week, and congratulations for exercising
          your musical skills!
        </p>
      </div>
      <div class="submit-form">
        <div class="entry-param">
          <label for="entryName">Entry Name</label>
          <input name="entryName" type="text" v-model="entry.entryName" />
        </div>
        <br />
        <div class="entry-param">
          <label
            ><input type="radio" value="upload" v-model="mp3Format" /> Upload
            MP3</label
          >
          <label
            ><input type="radio" value="external" v-model="mp3Format" /> Link
            MP3</label
          >
          <label v-show="entry.mp3Url"
            ><input type="radio" value="keep" v-model="mp3Format" /> Keep
            current MP3 file</label
          >
        </div>
        <div class="entry-param" v-if="mp3Format === 'keep'">
          <a :href="entry.mp3Url">Link to MP3</a>
        </div>
        <div class="entry-param" v-else-if="mp3Format === 'upload'">
          <label for="mp3">Upload MP3</label>
          <input
            name="mp3"
            type="file"
            @change="setFile('mp3', $event)"
            accept=".mp3"
          />
        </div>
        <div class="entry-param" v-else-if="mp3Format === 'external'">
          <label for="mp3Link"
            >If you have an external link to your submission (e.g. SoundCloud),
            you can enter that here.</label
          >
          <input name="mp3Link" type="text" v-model="mp3Link" />

          <div v-if="mp3LinkError()" class="error-message">
            {{ mp3LinkError() }}
          </div>
        </div>
        <br />
        <div class="entry-param">
          <label
            ><input type="radio" value="upload" v-model="pdfFormat" /> Upload
            PDF</label
          >
          <label v-show="entry.pdfUrl"
            ><input type="radio" value="keep" v-model="pdfFormat" /> Keep
            current PDF file</label
          >
        </div>
        <div class="entry-param" v-if="pdfFormat === 'keep'">
          <a :href="entry.pdfUrl">Link to PDF</a>
        </div>
        <div class="entry-param" v-else-if="pdfFormat === 'upload'">
          <label for="pdf">Upload PDF</label>
          <input
            name="pdf"
            type="file"
            @change="setFile('pdf', $event)"
            accept=".pdf"
          />
        </div>
        <br />
        <input
          :disabled="working"
          class="entry-param submit-button"
          type="submit"
          value="Submit Entry"
          @click="submit"
        />
      </div>
    </div>
  </div>
  <div v-else-if="mode === 'thanks'">
    <div id="content">
      <div class="submit-babble">
        <h2>Your entry has been recorded -- Good luck!</h2>
        <p>
          You can DM @8Bot the command
          <code>vote!status</code>
          to check the status of your entry!
        </p>
        <p>
          If you have any issues, let us know in #weekly-challenge-discussion,
          or DM one of our moderators.
        </p>
        <img width="500px" src="../static/kirb_thanks.png" />
      </div>
    </div>
  </div>
</template>

<style></style>
