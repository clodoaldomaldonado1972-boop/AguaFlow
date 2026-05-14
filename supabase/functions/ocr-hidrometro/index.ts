import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

serve(async (req) => {
  try {
    const payload = await req.json();

    // Webhook da tabela storage.objects (INSERT = novo upload)
    const record = payload.record;
    if (!record || record.bucket_id !== "fotos_hidrometros") {
      return new Response("Ignored", { status: 200 });
    }

    const filePath: string = record.name; // ex: "162/20260514_132942_AGUA.jpg"
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const openaiKey = Deno.env.get("OPENAI_API_KEY")!;

    if (!openaiKey) {
      console.error("OPENAI_API_KEY não configurada.");
      return new Response("Config error", { status: 500 });
    }

    const supabase = createClient(supabaseUrl, serviceKey);

    // Obtém URL pública da foto
    const { data: urlData } = supabase.storage
      .from("fotos_hidrometros")
      .getPublicUrl(filePath);
    const publicUrl = urlData.publicUrl;

    // Determina o tipo pelo nome do arquivo (ex: "...AGUA.jpg" ou "...GAS.jpg")
    const tipoModo = filePath.toUpperCase().includes("GAS") ? "gás" : "água";

    // Chama GPT-4o-mini Vision
    const ocrResponse = await fetch(
      "https://api.openai.com/v1/chat/completions",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${openaiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "gpt-4o-mini",
          messages: [
            {
              role: "user",
              content: [
                {
                  type: "text",
                  text:
                    `Esta é uma foto de um hidrômetro de ${tipoModo}. ` +
                    "Leia o número exibido no mostrador/visor do medidor. " +
                    "Retorne APENAS o número com até 2 casas decimais, ex: 1234.56. " +
                    "Não inclua texto, unidade ou explicação. " +
                    "Se não conseguir ler claramente, retorne: null",
                },
                {
                  type: "image_url",
                  image_url: { url: publicUrl, detail: "low" },
                },
              ],
            },
          ],
          max_tokens: 20,
          temperature: 0,
        }),
      }
    );

    if (!ocrResponse.ok) {
      const err = await ocrResponse.text();
      console.error("Erro na API OpenAI:", err);
      return new Response("OpenAI error", { status: 502 });
    }

    const ocrResult = await ocrResponse.json();
    const ocrText: string =
      ocrResult.choices?.[0]?.message?.content?.trim() ?? "";

    console.log(`OCR bruto para ${filePath}: "${ocrText}"`);

    if (!ocrText || ocrText.toLowerCase() === "null") {
      console.log("OCR não detectou número.");
      return new Response("OCR: no result", { status: 200 });
    }

    const valorOcr = parseFloat(ocrText.replace(",", "."));
    if (isNaN(valorOcr)) {
      console.log(`OCR retornou valor não numérico: ${ocrText}`);
      return new Response("OCR: invalid value", { status: 200 });
    }

    // Atualiza leituras.valor_leitura onde foto_url termina com o filePath
    const { error: updateError } = await supabase
      .from("leituras")
      .update({ valor_leitura: valorOcr })
      .like("foto_url", `%${filePath}`);

    if (updateError) {
      console.error("Erro ao atualizar leituras:", updateError.message);
      return new Response("DB update error", { status: 500 });
    }

    console.log(`OCR concluído: ${filePath} → ${valorOcr}`);
    return new Response(JSON.stringify({ filePath, valorOcr }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("Erro interno na Edge Function OCR:", err);
    return new Response("Internal error", { status: 500 });
  }
});
