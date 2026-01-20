import express from "express";
import {
  FetchDairyEntries,
  DeleteEntry,
  getTFTD,
  refetchAnalysis
} from "../Controllers/DiaryControllers.js";

const router = express.Router();

// ✅ THIS MUST MATCH FRONTEND
router.get("/fetchDetails", FetchDairyEntries);

router.delete("/deleteEntry", DeleteEntry);
router.get("/thoughtOfTheDay", getTFTD);
router.get("/refetchAnalysis", refetchAnalysis);

export default router;
