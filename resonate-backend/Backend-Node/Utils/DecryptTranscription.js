import crypto from "crypto";

export const decrypt_transcription = (encryptedText) => {
  if (!encryptedText) return "";

  try {
    const [ivHex, encryptedHex] = encryptedText.split(":");
    if (!ivHex || !encryptedHex) {
      throw new Error("Invalid encrypted text format");
    }

    const iv = Buffer.from(ivHex, "hex");
    const encrypted = Buffer.from(encryptedHex, "hex");

    const key = crypto.scryptSync(
      process.env.ENCRYPTION_KEY,
      "salt",
      32
    );

    const decipher = crypto.createDecipheriv(
      process.env.ENCRYPTION_ALGORITHM,
      key,
      iv
    );

    // ✅ IMPORTANT: Let Node handle padding
    let decrypted = decipher.update(encrypted, undefined, "utf8");
    decrypted += decipher.final("utf8");

    return decrypted;

  } catch (error) {
    console.error("Decryption error:", error.message);
    return "";
  }
};
