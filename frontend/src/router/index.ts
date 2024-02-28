import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "vote",
      component: () => import("../views/VotingView/"),
    },
    {
      path: "/edit/:id",
      name: "edit",
      component: () => import("../views/SubmissionView/"),
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("../views/AdminView/"),
    },
  ],
});

export default router;
