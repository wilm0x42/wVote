<script setup lang="ts">
import { RouterView } from "vue-router";
import banner from "./banner.png";
</script>

<template>
  <h1>
    <img :src="banner" alt="8BIT MUSIC THEORY WEEKLIES" />
  </h1>
  <div id="content">
    <RouterView />
  </div>
</template>

<style>
/* TODO: Split stuff 'cuz it's nice */
@font-face {
  font-family: font-ubuntu;
  src: url("@/static/ubuntu-regular.ttf");
}

body {
  font-family: font-ubuntu, Arial;
  font-size: 1.1em;
  color: white;
  margin: 0;
  padding: 0;
  background-color: #361536;
}

a {
  color: #ccccff;
}

h1 {
  background-color: #ff00ff;
  background: url("@/static/banner_background.png");
  background-repeat: repeat-x;
  color: white;
  font-size: 3em;
  margin: 0px;
  padding: 0px;
  width: 100%;
  height: 48px;
  text-shadow: 2px 2px black;
}

@media not screen and (min-width: 1024px) and (orientation: landscape) {
  .entries-container {
    width: 100%;
  }
}

.entry-list-toggle-enter-active,
.entry-list-toggle-leave-active {
  transition:
    opacity 0.15s,
    transform 0.15s;
}

.entry-list-toggle-enter,
.entry-list-toggle-leave-to {
  opacity: 0;
  transform: translateX(-50vw);
}

.entry-table {
  margin: auto;
  margin-top: 25px;
  overflow: auto;
  border-collapse: collapse;
}

.entry-table-header-row {
  position: sticky;
  top: 0px;
  background: rgba(141, 80, 141, 0.85);
  border: 1px solid #683168;
}

.entry-table-header {
  margin-right: 32px;
}

.entry-cell {
  font-size: 0.9em;
  padding: 0.25em;
  background-color: #361536;
  text-align: center;
  border: 1px solid #8d508d;
}

.entry-cell-selected {
  background-image: url("@/static/cat_head_bob.gif");
  background-repeat: no-repeat;
  background-size: cover;
}

.pdf-container {
  float: right;
  height: calc(100vh - 48px - 48px);
  background-image: linear-gradient(to bottom left, #8d508d, #683168);
  position: absolute;
  right: 0px;
  z-index: -1;
}

.pdf-color-invert {
  filter: invert(93%);
}

.pdf-container-small {
  display: none;
}

@media only screen and (min-width: 1024px) and (orientation: landscape) {
  .pdf-container-small {
    width: 20%;
    display: block;
  }
}

.pdf-container-full {
  width: 100%;
  display: block;
}

.pdf-viewer-welcome {
  display: block;
  margin: auto;
  width: 100%;
  text-align: center;
  position: relative;
  top: 50%;
  transform: translate(0%, -50%);
}

.pdf-alt {
  display: block;
  margin: auto;
  width: 100%;
  text-align: center;
  position: relative;
  top: 50%;
  transform: translate(0%, -50%);
}

.pdf-viewer-live {
  display: block;
  margin: auto;
  width: 100%;
  height: 100%;
}

.viewer-control-bar {
  background-color: #ff00ff;
  background: url("@/static/banner_background.png");
  background-repeat: repeat-x;

  margin: 0px;
  padding: 0px;
  height: 48px;
  width: 100vw;
  position: fixed;
  top: calc(100vh - 48px);
  border-collapse: collapse;
}

.viewer-control {
  padding: 0px;
  font-size: 0.8em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vote-star-widget {
  border-collapse: collapse;
  margin: 0px;
  padding: 0px;
}

.vote-star-cell {
  margin: 0px;
  padding: 0px;
}

.vote-star {
  background: none;
  border: none;
  font-size: 1.2em;
  padding: 0px;
  margin-right: 1px;
  width: 1.2em;
  height: 1.2em;
  overflow: hidden;
  position: relative;
  top: 2px;
}

.vote-star-img {
  width: 1.2em;
  margin: 0px;
  padding: 0px;
}

.vote-star-bottom-label {
  height: 0.75em;
  margin: 0px 2px 0px 0px;
  text-align: center;
  position: relative;
  top: -4px;
}

.vote-stars-bottom-panel {
  display: none;
}

@media only screen and (min-width: 1280px) and (orientation: landscape) {
  .vote-stars-bottom-panel {
    display: block;
  }
}

.vote-label {
  margin: 0px;
  padding: 2px;
  white-space: nowrap;
  float: right;
}

.vote-submit-area {
  width: 400px;
  margin: auto;
  padding: 50px;
  text-align: center;
}

.progress-img {
  text-align: center;
}

.submit-babble {
  text-align: center;
}

.tooltip {
  display: block !important;
  z-index: 10000;
}

.tooltip .tooltip-inner {
  background: black;
  color: white;
  border-radius: 16px;
  padding: 5px 10px 4px;
}

.tooltip .tooltip-arrow {
  width: 0;
  height: 0;
  border-style: solid;
  position: absolute;
  margin: 5px;
  border-color: black;
}

.tooltip[x-placement^="top"] {
  margin-bottom: 5px;
}

.tooltip[x-placement^="top"] .tooltip-arrow {
  border-width: 5px 5px 0 5px;
  border-left-color: transparent !important;
  border-right-color: transparent !important;
  border-bottom-color: transparent !important;
  bottom: -5px;
  left: calc(50% - 5px);
  margin-top: 0;
  margin-bottom: 0;
}

.tooltip[x-placement^="bottom"] {
  margin-top: 5px;
}

.tooltip[x-placement^="bottom"] .tooltip-arrow {
  border-width: 0 5px 5px 5px;
  border-left-color: transparent !important;
  border-right-color: transparent !important;
  border-top-color: transparent !important;
  top: -5px;
  left: calc(50% - 5px);
  margin-top: 0;
  margin-bottom: 0;
}

.tooltip[x-placement^="right"] {
  margin-left: 5px;
}

.tooltip[x-placement^="right"] .tooltip-arrow {
  border-width: 5px 5px 5px 0;
  border-left-color: transparent !important;
  border-top-color: transparent !important;
  border-bottom-color: transparent !important;
  left: -5px;
  top: calc(50% - 5px);
  margin-left: 0;
  margin-right: 0;
}

.tooltip[x-placement^="left"] {
  margin-right: 5px;
}

.tooltip[x-placement^="left"] .tooltip-arrow {
  border-width: 5px 0 5px 5px;
  border-top-color: transparent !important;
  border-right-color: transparent !important;
  border-bottom-color: transparent !important;
  right: -5px;
  top: calc(50% - 5px);
  margin-left: 0;
  margin-right: 0;
}

.tooltip[aria-hidden="true"] {
  visibility: hidden;
  opacity: 0;
  transition:
    opacity 0.15s,
    visibility 0.15s;
}

.tooltip[aria-hidden="false"] {
  visibility: visible;
  opacity: 1;
  transition: opacity 0.15s;
}
</style>
