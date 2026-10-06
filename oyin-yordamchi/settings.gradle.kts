rootProject.name = "oyin-yordamchi"

// Qatlamlar: core (o'yindan mustaqil) <- cards (karta o'yinlari uchun umumiy) <- games/*
include("core")
include("cards")
include("games:durak")
include("desktop")
