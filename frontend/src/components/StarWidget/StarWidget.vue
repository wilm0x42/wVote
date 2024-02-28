<script setup lang="ts">
import interfaceStarYes from "./interface-star-yes.svg";
import interfaceStarNo from "./interface-star-no.svg";

const props = defineProps<{
  modelValue: number;
  helptipdefs: Record<number, string>;
}>();
const emit = defineEmits<{ "update:modelValue": [number] }>();

const vote = (newValue: number) => {
  if (props.modelValue == newValue) {
    emit("update:modelValue", 0);
  } else {
    emit("update:modelValue", newValue);
  }
};
</script>

<template>
  <table class="vote-star-widget" cellpadding="0">
    <tr>
      <td
        v-for="starNum in [1, 2, 3, 4, 5]"
        :key="starNum"
        class="vote-star-cell"
      >
        <span v-tooltip="helptipdefs[starNum]">
          <button @click="vote(starNum)" class="vote-star">
            <img
              class="vote-star-img"
              v-if="modelValue >= starNum"
              :src="interfaceStarYes"
            />
            <img class="vote-star-img" :src="interfaceStarNo" v-else /></button
        ></span>
      </td>
    </tr>
  </table>
</template>
