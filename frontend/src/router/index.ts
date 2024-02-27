import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "vote",
      component: () => import("../views/VotingView.vue"),
    },
    {
      path: "/edit",
      name: "edit",
      component: () => import("../views/SubmissionView.vue"),
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("../views/AdminView.vue"),
    },
  ],
});

export default router;
