-- CreateTable
CREATE TABLE "EmojiSent" (
    "id" SERIAL NOT NULL,
    "emoji_id" VARCHAR(20) NOT NULL,
    "user_id" VARCHAR(20) NOT NULL,
    "guild_id" VARCHAR(20) NOT NULL,
    "channel_id" VARCHAR(20) NOT NULL,
    "sent_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "EmojiSent_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "EmojiSent_emoji_id_sent_at_user_id_guild_id_channel_id_idx" ON "EmojiSent"("emoji_id", "sent_at", "user_id", "guild_id", "channel_id");
