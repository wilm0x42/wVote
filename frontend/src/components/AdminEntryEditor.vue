<script setup lang="ts">
import type { AdminEntry } from "@/types";
import { ref, defineProps, reactive } from "vue";

const props = defineProps<{
  authKey: string;
  entry: AdminEntry;
  nextWeek: boolean;
}>();
const emit = defineEmits(["editedentry"]);

const editableEntry = reactive(props.entry);

const working = ref(false);
const pdfFormat = ref<"keep" | "upload">("upload");
const mp3Format = ref<"keep" | "upload" | "external">("upload");
const mp3File = ref<null | {
  fileName: string;
  file: File;
}>(null);
const mp3Link = ref("");
const pdfFile = ref<null | {
  fileName: string;
  file: File;
}>(null);

const hide = ref(true);
const deleteEntry = ref(false);

const setFile = (type: "pdf" | "mp3", event: Event) => {
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

const submit = async () => {
  working.value = true;

  try {
    const formData = new FormData();

    if (deleteEntry.value) {
      formData.append("deleteEntry", "true");
    } else {
      if (props.entry.entryName.length === 0) {
        throw new Error("Please set an entry name");
      }

      if (props.entry.entrantName.length === 0) {
        throw new Error("Please set an entry name");
      }

      formData.append("entryName", props.entry.entryName);
      formData.append("entrantName", props.entry.entrantName);
      if (props.entry.entryNotes) {
        formData.append("entryNotes", props.entry.entryNotes);
      }

      if (pdfFormat.value === "upload") {
        if (!pdfFile.value) {
          throw new Error(
            "You've chosen to upload a PDF but haven't picked one.",
          );
        }
        formData.append("pdf", pdfFile.value.file, pdfFile.value.fileName);
      }

      if (mp3Format.value === "external") {
        // WARN: We're not checking for invalid hosts.
        formData.append("mp3Link", mp3Link.value);
      } else if (mp3Format.value === "upload") {
        if (!mp3File.value) {
          throw new Error(
            "You've chosen to upload an MP3 but haven't picked one.",
          );
        }
        formData.append("mp3", mp3File.value.file, mp3File.value.fileName);
      }
    }

    // TODO: Remove `authkey` and only pass it in header
    let request = await fetch(
      "/api/edit/post/" + props.entry.uuid + "/" + props.authKey,
      {
        method: "POST",
        body: formData,
        headers: {
          authorization: `Bearer ${props.authKey}`,
        },
      },
    );

    if (!request.ok) {
      throw new Error("Something went wrong: " + (await request.text()));
    }

    emit("editedentry");
  } catch (e) {
    alert((e as Error).toString());
  } finally {
    working.value = false;
  }
};
</script>

<template>
  <div
    class="admin-entry-form"
    :class="{
      'form-current-week': !nextWeek,
      'form-next-week': nextWeek,
      'form-invalid': !entry.isValid,
    }"
  >
    <h3 @click="hide = !hide">
      Entry for {{ nextWeek ? "NEXT" : "CURRENT" }} week ({{
        entry.isValid ? "valid" : "invalid!"
      }}) - {{ entry.entrantName }}
    </h3>
    <div v-show="!hide">
      <div class="admin-entry-param">
        <label for="entryName">Entry Name</label>
        <input name="entryName" type="text" v-model="editableEntry.entryName" />
      </div>
      <br />
      <div class="admin-entry-param">
        <label for="entrantName">Discord Username</label>
        <input
          name="entrantName"
          type="text"
          v-model="editableEntry.entrantName"
        />
      </div>
      <br />
      <div class="admin-entry-param">
        <label for="entryNotes">Additional Notes</label>
        <input
          name="entryNotes"
          type="text"
          v-model="editableEntry.entryNotes"
        />
      </div>
      <br />
      <div class="admin-entry-param">
        <label
          ><input type="radio" value="keep" v-model="mp3Format" /> Keep current
          MP3 file</label
        >
        <label
          ><input type="radio" value="upload" v-model="mp3Format" /> Upload
          MP3</label
        >
        <label
          ><input type="radio" value="external" v-model="mp3Format" /> Link
          MP3</label
        >
      </div>
      <div class="admin-entry-param" v-if="mp3Format === 'keep'">
        <a :href="entry.mp3Url">Link to MP3</a>
      </div>
      <div class="admin-entry-param" v-else-if="mp3Format === 'upload'">
        <label for="mp3">Upload MP3</label>
        <input name="mp3" type="file" @change="setFile('mp3', $event)" />
      </div>
      <div class="admin-entry-param" v-else-if="mp3Format === 'external'">
        <label for="mp3Link"
          >If you have an external link to your submission (e.g. SoundCloud),
          you can enter that here.</label
        >
        <input name="mp3Link" type="text" v-model="mp3Link" />
      </div>
      <br />
      <div class="admin-entry-param">
        <label
          ><input type="radio" value="keep" v-model="pdfFormat" /> Keep current
          PDF file</label
        >
        <label
          ><input type="radio" value="upload" v-model="pdfFormat" /> Upload
          PDF</label
        >
      </div>
      <div class="admin-entry-param" v-if="pdfFormat === 'keep'">
        <a :href="entry.pdfUrl">Link to PDF</a>
      </div>
      <div class="admin-entry-param" v-else-if="pdfFormat === 'upload'">
        <label for="pdf">Upload PDF</label>
        <input name="pdf" type="file" @change="setFile('pdf', $event)" />
      </div>
      <br />
      <div class="admin-entry-param">
        <label for="deleteEntry">Delete Entry</label>
        <input type="checkbox" name="deleteEntry" v-model="deleteEntry" />
      </div>
      <br />
      <input
        type="submit"
        value="Submit Entry"
        class="admin-entry-param admin-submit-button"
        @click="submit"
      />
    </div>
  </div>
</template>
