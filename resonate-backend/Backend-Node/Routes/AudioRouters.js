import express from "express";
import multer from "multer";
import {
  FetchEntryDetails,
  GetAudio,
  SaveAudio,
  SetTitle,
  getAnalysis
} from "../Controllers/AudioController.js";

const router = express.Router();

// 🔥 MULTER SETUP (REQUIRED)
const upload = multer({
  storage: multer.memoryStorage()
});

// ✅ THIS MUST MATCH FRONTEND CALL
router.get("/fetchDetails", FetchEntryDetails);

// 🔥 AUDIO UPLOAD ROUTE (FIXED)
router.post("/saveAudio", upload.single("audio"), SaveAudio);

router.post("/getAudio", GetAudio);
router.patch("/setTitle", SetTitle);
router.post("/runAnalysis", getAnalysis);

export default router;
