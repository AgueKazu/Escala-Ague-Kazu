"use client";

import { useEffect, useState } from "react";
import { supabase, variaveisConfiguradas } from "@/lib/supabase";
import type { Escala, Funcionario, Turno } from "@/lib/tipos";
import {
  DIAS_SEMANA,
  diaMes,
  diasDaSemana,
  hojeISO,
  horaCurta,
  inicioDaSemana,
  paraData,
  rotuloDia,
  somarDias,
} from "@/lib/datas";

type CelulaAberta = { data: string; turno: Turno };

export default function EscalaDaSemana() {
  const [segunda, setSegunda] = useState(() => inicioDaSemana(hojeISO()));
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [escalas, setEscalas] = useState<Escala[]>([]);
  // Semana cujas escalas já vieram do banco; diferente da atual = carregando.
  const [semanaCarregada, setSemanaCarregada] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(
    variaveisConfiguradas() ? null : "As variáveis do Supabase não foram configuradas.",
  );
  const [aberta, setAberta] = useState<CelulaAberta | null>(null);
  const [ocupados, setOcupados] = useState<Set<string>>(new Set());

  const dias = diasDaSemana(segunda);
  const domingo = dias[6];
  const hoje = hojeISO();
  const carregando = semanaCarregada !== segunda;

  // Turnos e funcionários: carregados uma vez.
  useEffect(() => {
    if (!variaveisConfiguradas()) return;
    const db = supabase();
    Promise.all([
      db.from("turnos").select("id, nome, hora_inicio, hora_fim, ordem").order("ordem"),
      db.from("funcionarios").select("id, nome, funcao, telefone, cpf, ativo").order("nome"),
    ]).then(([t, f]) => {
      if (t.error || f.error) {
        setErro(`Não foi possível carregar os dados: ${(t.error ?? f.error)?.message}`);
        return;
      }
      setTurnos(t.data as Turno[]);
      setFuncionarios(f.data as Funcionario[]);
    });
  }, []);

  // Escala da semana: recarrega ao trocar de semana.
  useEffect(() => {
    if (!variaveisConfiguradas()) return;
    let valido = true;
    supabase()
      .from("escalas")
      .select("id, data, turno_id, funcionario_id")
      .gte("data", segunda)
      .lte("data", somarDias(segunda, 6))
      .then(({ data, error }) => {
        if (!valido) return;
        if (error) setErro(`Não foi possível carregar a escala: ${error.message}`);
        else setEscalas(data as Escala[]);
        setSemanaCarregada(segunda);
      });
    return () => {
      valido = false;
    };
  }, [segunda]);

  const porId = new Map(funcionarios.map((f) => [f.id, f]));

  function escaladosNa(data: string, turnoId: string): Escala[] {
    return escalas
      .filter((e) => e.data === data && e.turno_id === turnoId)
      .sort((a, b) =>
        (porId.get(a.funcionario_id)?.nome ?? "").localeCompare(
          porId.get(b.funcionario_id)?.nome ?? "",
        ),
      );
  }

  async function alternar(data: string, turnoId: string, funcionarioId: string) {
    const chave = `${data}|${turnoId}|${funcionarioId}`;
    if (ocupados.has(chave)) return;
    setOcupados((s) => new Set(s).add(chave));
    setErro(null);

    const existente = escalas.find(
      (e) => e.data === data && e.turno_id === turnoId && e.funcionario_id === funcionarioId,
    );
    const db = supabase().from("escalas");
    if (existente) {
      const { error } = await db.delete().eq("id", existente.id);
      if (error) setErro(`Não foi possível remover: ${error.message}`);
      else setEscalas((lista) => lista.filter((e) => e.id !== existente.id));
    } else {
      const { data: nova, error } = await db
        .insert({ data, turno_id: turnoId, funcionario_id: funcionarioId })
        .select("id, data, turno_id, funcionario_id")
        .single();
      if (error) setErro(`Não foi possível salvar: ${error.message}`);
      else setEscalas((lista) => [...lista, nova as Escala]);
    }

    setOcupados((s) => {
      const n = new Set(s);
      n.delete(chave);
      return n;
    });
  }

  // Funcionários ativos agrupados por função, para a janela de escolha.
  const ativos = funcionarios.filter((f) => f.ativo);
  const grupos = new Map<string, Funcionario[]>();
  for (const f of ativos) {
    grupos.set(f.funcao, [...(grupos.get(f.funcao) ?? []), f]);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Escala da semana</h1>

      <div className="flex items-center gap-2">
        <button
          className="botao-secundario px-3"
          onClick={() => setSegunda(somarDias(segunda, -7))}
          aria-label="Semana anterior"
        >
          ◀
        </button>
        <div className="flex-1 text-center">
          <p className="font-semibold">
            {diaMes(segunda)} a {diaMes(domingo)}
          </p>
          {segunda !== inicioDaSemana(hoje) && (
            <button
              className="text-sm underline"
              style={{ color: "var(--cor-principal)" }}
              onClick={() => setSegunda(inicioDaSemana(hoje))}
            >
              Voltar para esta semana
            </button>
          )}
        </div>
        <button
          className="botao-secundario px-3"
          onClick={() => setSegunda(somarDias(segunda, 7))}
          aria-label="Semana seguinte"
        >
          ▶
        </button>
      </div>

      {erro && <p className="cartao border-red-300 text-red-700">{erro}</p>}

      <p className="text-sm text-neutral-600">Toque em um quadro para escolher quem trabalha.</p>

      <div className="cartao overflow-x-auto p-0">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 z-[1] bg-white p-2 text-left">Turno</th>
              {dias.map((d) => (
                <th
                  key={d}
                  className={`min-w-[96px] p-2 text-center ${d === hoje ? "bg-amber-50" : ""}`}
                >
                  {rotuloDia(d)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {turnos.map((t) => (
              <tr key={t.id} className="border-t border-neutral-200">
                <th className="sticky left-0 z-[1] bg-white p-2 text-left align-top">
                  <span className="block font-semibold">{t.nome}</span>
                  <span className="block text-xs font-normal text-neutral-500">
                    {horaCurta(t.hora_inicio)}–{horaCurta(t.hora_fim)}
                  </span>
                </th>
                {dias.map((d) => {
                  const lista = escaladosNa(d, t.id);
                  return (
                    <td key={d} className={`p-1 align-top ${d === hoje ? "bg-amber-50" : ""}`}>
                      <button
                        className="flex min-h-[88px] w-full flex-col items-start gap-0.5 rounded-lg border border-dashed border-neutral-300 p-1.5 text-left active:bg-neutral-100 disabled:opacity-50"
                        onClick={() => setAberta({ data: d, turno: t })}
                        disabled={carregando}
                      >
                        {lista.length === 0 ? (
                          <span className="text-neutral-400">+ escalar</span>
                        ) : (
                          lista.map((e) => {
                            const f = porId.get(e.funcionario_id);
                            return (
                              <span key={e.id} className="leading-tight">
                                {f ? f.nome.split(" ")[0] : "?"}
                              </span>
                            );
                          })
                        )}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {aberta && (
        <div
          className="fixed inset-0 z-20 flex items-end justify-center bg-black/40 sm:items-center"
          onClick={() => setAberta(null)}
        >
          <div
            className="max-h-[85vh] w-full max-w-md overflow-y-auto rounded-t-2xl bg-white p-4 sm:rounded-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-bold">
              {aberta.turno.nome} · {DIAS_SEMANA[paraData(aberta.data).getDay()]}{" "}
              {diaMes(aberta.data)}
            </h2>
            <p className="mb-3 text-sm text-neutral-600">
              Marque quem trabalha. Salva automaticamente.
            </p>

            {ativos.length === 0 && (
              <p className="text-neutral-600">Nenhum funcionário ativo. Cadastre na tela Equipe.</p>
            )}

            {[...grupos.entries()].map(([funcao, pessoas]) => (
              <div key={funcao} className="mb-3">
                <p className="mb-1 text-sm font-semibold uppercase text-neutral-500">{funcao}</p>
                <div className="space-y-2">
                  {pessoas.map((f) => {
                    const marcado = escalas.some(
                      (e) =>
                        e.data === aberta.data &&
                        e.turno_id === aberta.turno.id &&
                        e.funcionario_id === f.id,
                    );
                    const chave = `${aberta.data}|${aberta.turno.id}|${f.id}`;
                    return (
                      <label
                        key={f.id}
                        className={`flex min-h-[52px] cursor-pointer items-center gap-3 rounded-xl border px-3 py-2 ${
                          marcado ? "border-neutral-500 bg-neutral-50" : "border-neutral-200"
                        } ${ocupados.has(chave) ? "opacity-50" : ""}`}
                      >
                        <input
                          type="checkbox"
                          className="h-6 w-6"
                          style={{ accentColor: "var(--cor-principal)" }}
                          checked={marcado}
                          disabled={ocupados.has(chave)}
                          onChange={() => alternar(aberta.data, aberta.turno.id, f.id)}
                        />
                        <span className="text-base">{f.nome}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}

            {/* Quem está escalado mas foi desativado depois */}
            {escaladosNa(aberta.data, aberta.turno.id)
              .map((e) => porId.get(e.funcionario_id))
              .filter((f): f is Funcionario => Boolean(f && !f.ativo))
              .map((f) => (
                <div
                  key={f.id}
                  className="mb-2 flex items-center justify-between rounded-xl border border-neutral-200 px-3 py-2"
                >
                  <span>{f.nome} (desativado)</span>
                  <button
                    className="botao-secundario px-3 py-2 text-sm"
                    onClick={() => alternar(aberta.data, aberta.turno.id, f.id)}
                  >
                    Remover
                  </button>
                </div>
              ))}

            <button className="botao mt-2 w-full" onClick={() => setAberta(null)}>
              Pronto
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
