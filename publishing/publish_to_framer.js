#!/usr/bin/env node
/**
 * Framer CMS Publisher — publishes approved articles to Framer via the framer-api SDK.
 *
 * Adapted from AY-AY-AY-AY/athenahq-marketing src/lib/integrations/framer-simple-api.ts
 *
 * Usage:
 *   node --input-type=module publish_to_framer.js --config ../brand-context/config.json --article path/to/article.md --title "Article Title" --slug "article-slug" [--summary "..."] [--author "..."] [--draft]
 *   node --input-type=module publish_to_framer.js --config ../brand-context/config.json --batch path/to/pipeline_summary.json
 *
 * Environment:
 *   FRAMER_API_KEY — Framer project API key
 *   FRAMER_PROJECT_URL — Framer project URL (or set in config.json)
 */

import { connect } from "framer-api";
import fs from "fs";
import path from "path";

function loadConfig(configPath) {
  const raw = fs.readFileSync(configPath, "utf-8");
  return JSON.parse(raw);
}

function createSlug(rawValue) {
  return rawValue
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

function findField(fields, key) {
  const namesByKey = {
    title: ["title", "name", "headline"],
    content: ["content", "body", "article", "text"],
    summary: ["summary", "description", "excerpt", "meta"],
    author: ["author", "writer"],
    publishedDate: ["publish", "published", "date"],
  };

  const patterns = namesByKey[key] || [];

  const byName = fields.find((f) => {
    const lower = f.name.toLowerCase();
    return patterns.some((p) => lower.includes(p));
  });

  if (byName) return byName;

  if (key === "content") return fields.find((f) => f.type === "formattedText");
  if (key === "publishedDate") return fields.find((f) => f.type === "date");
  return fields.find((f) => f.type === "string");
}

function buildFieldData(fields, input) {
  const fieldData = {};

  const titleField = findField(fields, "title");
  const contentField = findField(fields, "content");
  const summaryField = findField(fields, "summary");
  const authorField = findField(fields, "author");
  const dateField = findField(fields, "publishedDate");

  if (titleField) {
    fieldData[titleField.id] = { type: "string", value: input.title };
  }

  if (contentField) {
    if (contentField.type === "formattedText") {
      fieldData[contentField.id] = {
        type: "formattedText",
        value: input.content,
        contentType: "markdown",
      };
    } else {
      fieldData[contentField.id] = { type: contentField.type, value: input.content };
    }
  }

  if (summaryField && input.summary) {
    fieldData[summaryField.id] = { type: "string", value: input.summary };
  }

  if (authorField && input.author) {
    fieldData[authorField.id] = { type: "string", value: input.author };
  }

  if (dateField) {
    fieldData[dateField.id] = { type: "date", value: new Date().toISOString() };
  }

  return fieldData;
}

async function publishArticle(projectUrl, apiKey, collectionId, input) {
  const target =
    projectUrl.includes(".") || projectUrl.includes("/")
      ? `https://${projectUrl}`
      : projectUrl;

  const framer = await connect(target, apiKey);

  try {
    const collection = await framer.getCollection(collectionId);
    if (!collection) throw new Error("Collection not found");

    const fields = await collection.getFields();
    const slug = createSlug(input.slug || input.title);

    await collection.addItems([
      {
        slug,
        draft: input.draft || false,
        fieldData: buildFieldData(fields, input),
      },
    ]);

    let publishedUrl = null;

    if (!input.draft) {
      const publishResult = await framer.publish();
      const deployed = await framer
        .deploy(publishResult.deployment.id)
        .catch(() => []);

      const hostnames = deployed.length ? deployed : publishResult.hostnames;
      const hostname = hostnames.find((h) => h.isPrimary && h.isPublished)
        || hostnames.find((h) => h.isPublished)
        || hostnames[0];

      if (hostname) {
        const collectionSlug = createSlug(collection.name);
        publishedUrl = `https://${hostname.hostname}/${collectionSlug}/${slug}`;
      }
    }

    return { success: true, slug, publishedUrl, draft: input.draft || false };
  } finally {
    await framer.disconnect();
  }
}

async function main() {
  const args = process.argv.slice(2);
  const getArg = (flag) => {
    const idx = args.indexOf(flag);
    return idx !== -1 && idx + 1 < args.length ? args[idx + 1] : null;
  };
  const hasFlag = (flag) => args.includes(flag);

  const configPath = getArg("--config") || "../brand-context/config.json";
  const config = loadConfig(configPath);
  const framerConfig = config.publishing?.framer || {};

  const projectUrl =
    process.env.FRAMER_PROJECT_URL ||
    framerConfig.project_url ||
    "";
  const apiKey =
    process.env[framerConfig.api_key_env || "FRAMER_API_KEY"] ||
    process.env.FRAMER_API_KEY ||
    "";
  const collectionId = framerConfig.collection_id || "";

  if (!projectUrl || !apiKey || !collectionId) {
    console.error(
      JSON.stringify({
        error:
          "Missing Framer config. Set FRAMER_PROJECT_URL, FRAMER_API_KEY, and publishing.framer.collection_id in config.",
      })
    );
    process.exit(1);
  }

  const batchFile = getArg("--batch");

  if (batchFile) {
    const summary = JSON.parse(fs.readFileSync(batchFile, "utf-8"));
    const staged = (summary.articles_staged || []).filter((a) => a.approved);

    if (!staged.length) {
      console.log(JSON.stringify({ message: "No approved articles to publish", count: 0 }));
      return;
    }

    const results = [];
    for (const article of staged) {
      const content = fs.readFileSync(article.article_file, "utf-8");
      const titleMatch = content.match(/^#\s+(.+)$/m);
      const title = titleMatch ? titleMatch[1] : article.prompt;

      try {
        const result = await publishArticle(projectUrl, apiKey, collectionId, {
          title,
          content,
          slug: article.prompt,
          author: config.publishing?.author_name || "",
          draft: false,
        });
        results.push({ prompt: article.prompt, ...result });
      } catch (err) {
        results.push({ prompt: article.prompt, success: false, error: err.message });
      }
    }

    console.log(JSON.stringify({ published: results.length, results }));
    return;
  }

  const articlePath = getArg("--article");
  if (!articlePath) {
    console.error(JSON.stringify({ error: "Provide --article or --batch" }));
    process.exit(1);
  }

  const content = fs.readFileSync(articlePath, "utf-8");
  const title = getArg("--title") || content.match(/^#\s+(.+)$/m)?.[1] || "Untitled";
  const slug = getArg("--slug") || title;
  const summary = getArg("--summary") || "";
  const author = getArg("--author") || config.publishing?.author_name || "";
  const draft = hasFlag("--draft");

  try {
    const result = await publishArticle(projectUrl, apiKey, collectionId, {
      title,
      content,
      slug,
      summary,
      author,
      draft,
    });
    console.log(JSON.stringify(result));
  } catch (err) {
    console.error(JSON.stringify({ error: err.message }));
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(JSON.stringify({ error: err.message }));
  process.exit(1);
});
