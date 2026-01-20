import dotenv from "dotenv";
dotenv.config(); // MUST BE FIRST



import express from "express";

import cors from "cors";

import connectDb from "./Utils/db.js";

import AudioRouter from "./Routes/AudioRouters.js";
import DiaryRouter from "./Routes/DiaryRouter.js";
import InsightsRouter from "./Routes/InsightsRouter.js";
import GoalRouter from "./Routes/GoalRouter.js";


connectDb();

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("Server running");
});
console.log("SUPABASE_URL:", process.env.SUPABASE_URL);
console.log("SUPABASE_SERVICE_ROLE_KEY:", !!process.env.SUPABASE_SERVICE_ROLE_KEY);

app.use("/audio", AudioRouter);
app.use("/diary", DiaryRouter);
app.use("/insights", InsightsRouter);
app.use("/goals", GoalRouter);

app.listen(5000, () => {
  console.log("App listening on port 5000!");
});
