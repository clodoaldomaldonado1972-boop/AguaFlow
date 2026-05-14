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
    const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY")!;

    if (!anthropicKey) {
      console.error("ANTHROPIC_API_KEY não configurada.");
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

    // Chama Claude claude-opus-4-7 Vision
    const ocrResponse = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": anthropicKey,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: "claude-opus-4-7",
        max_tokens: 50,
        messages: [
          {
            role: "user",
            content: [
              {
                type: "image",
                source: {
                  type: "url",
                  url: publicUrl,
                },
              },
              {
                type: "text",
                text:
                  `Esta é uma foto de um hidrômetro de ${tipoModo}. ` +
                  "Leia o número exibido no mostrador/visor do medidor. " +
                  "Os dígitos em vermelho (ou em cor diferente dos demais) representam as casas decimais — inclua-os após o ponto decimal. " +
                  "Retorne APENAS o número com até 3 casas decimais usando ponto como separador decimal, ex: 328.936. " +
                  "Não inclua vírgula, texto, unidade ou explicação. " +
                  "Se não conseguir ler claramente, retorne: null",
              },
            ],
          },
        ],
      }),
    });

    if (!ocrResponse.ok) {
      const err = await ocrResponse.text();
      console.error("Erro na API Anthropic:", err);
      return new Response("Anthropic API error", { status: 502 });
    }

    const ocrResult = await ocrResponse.json();
    const ocrText: string =
      ocrResult.content?.[0]?.text?.trim() ?? "";

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
