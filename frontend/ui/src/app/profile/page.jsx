"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../../../lib/supabase/client";
import Header from "../../../components/ui/Header";
import BasicInfo from "../../../components/Profile/BasicInfo";
import AssetsSection from "../../../components/Profile/AssetsSection";
import LiabilitiesSection from "../../../components/Profile/LiabilitiesSection";
import PortfolioSection from "../../../components/Profile/PortfolioSection";
import AnalysisHistory from "../../../components/Profile/AnalysisHistory";

const INITIAL_CUSTOMER = {
  customer_id: "",
  name: null,
  age: null,
  annual_income: null,
  email: null,
  phone_number: null,
  number_of_dependents: null,
  investor_type: null,
};

function toNullableString(value) {
  if (value === null || value === undefined) {
    return null;
  }

  const normalized = String(value).trim();
  return normalized === "" ? null : normalized;
}

function toNullableInteger(value) {
  const normalized = toNullableString(value);
  if (normalized === null) {
    return null;
  }

  const parsed = Number.parseInt(normalized, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

function toNullableFloat(value) {
  const normalized = toNullableString(value);
  if (normalized === null) {
    return null;
  }

  const parsed = Number.parseFloat(normalized);
  return Number.isNaN(parsed) ? null : parsed;
}

function toNullableDate(value) {
  const normalized = toNullableString(value);
  if (!normalized) {
    return null;
  }
  return normalized;
}

function getDisplayName(user) {
  return toNullableString(user?.user_metadata?.full_name);
}

function formatCurrency(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

function buildHoldingsMap(holdings) {
  return holdings.reduce((acc, holding) => {
    const key = holding.portfolio_id;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(holding);
    return acc;
  }, {});
}

export default function ProfilePage() {
  const router = useRouter();
  const [authUser, setAuthUser] = useState(null);
  const [customer, setCustomer] = useState(INITIAL_CUSTOMER);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [assets, setAssets] = useState([]);
  const [liabilities, setLiabilities] = useState([]);
  const [portfolios, setPortfolios] = useState([]);
  const [holdingsByPortfolio, setHoldingsByPortfolio] = useState({});
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("basic");

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError("");

    const supabase = createClient();
    const { data: userData, error: userError } = await supabase.auth.getUser();

    if (userError || !userData?.user) {
      router.push("/login");
      return;
    }

    const user = userData.user;
    setAuthUser(user);

    const { data: customerData, error: customerError } = await supabase
      .from("customers")
      .select("*")
      .eq("customer_id", user.id)
      .maybeSingle();

    if (customerError) {
      setError(customerError.message || "Unable to load profile.");
      setLoading(false);
      return;
    }

    let currentCustomer = customerData;
    if (!currentCustomer) {
      const newCustomer = {
        customer_id: user.id,
        name: getDisplayName(user),
        email: user.email ?? null,
      };

      const { data: insertedCustomer, error: insertError } = await supabase
        .from("customers")
        .insert(newCustomer)
        .select("*")
        .single();

      if (insertError) {
        setError(insertError.message || "Unable to create profile.");
        setLoading(false);
        return;
      }

      currentCustomer = insertedCustomer;
    }

    const [{ data: assetsData, error: assetsError }, { data: liabilitiesData, error: liabilitiesError }, { data: portfoliosData, error: portfoliosError }, { data: analysisData, error: analysisError }] =
      await Promise.all([
        supabase.from("customer_assets").select("*").eq("customer_id", user.id).order("asset_id", { ascending: false }),
        supabase.from("customer_liabilities").select("*").eq("customer_id", user.id).order("liability_id", { ascending: false }),
        supabase.from("portfolios").select("*").eq("customer_id", user.id).order("portfolio_name", { ascending: true }),
        supabase
          .from("analysis_history")
          .select("*")
          .eq("customer_id", user.id)
          .order("date_of_analysis", { ascending: false }),
      ]);

    if (assetsError || liabilitiesError || portfoliosError || analysisError) {
      setError(
        assetsError?.message ||
          liabilitiesError?.message ||
          portfoliosError?.message ||
          analysisError?.message ||
          "Unable to load profile dashboard."
      );
      setLoading(false);
      return;
    }

    const portfolioIds = (portfoliosData ?? []).map((portfolio) => portfolio.portfolio_id);
    let holdingsMap = {};
    if (portfolioIds.length > 0) {
      const { data: holdingsData, error: holdingsError } = await supabase
        .from("portfolio_holdings")
        .select("*")
        .in("portfolio_id", portfolioIds)
        .order("ticker", { ascending: true });

      if (holdingsError) {
        setError(holdingsError.message || "Unable to load holdings.");
        setLoading(false);
        return;
      }

      holdingsMap = buildHoldingsMap(holdingsData ?? []);
    }

    setCustomer(currentCustomer ?? INITIAL_CUSTOMER);
    setAssets(assetsData ?? []);
    setLiabilities(liabilitiesData ?? []);
    setPortfolios(portfoliosData ?? []);
    setHoldingsByPortfolio(holdingsMap);
    setAnalysisHistory(analysisData ?? []);
    setLoading(false);
  }, [router]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const saveBasicInfo = async (formData) => {
    const customerId = authUser?.id;
    if (!customerId) {
      return { error: "You need to log in again." };
    }

    setSaving(true);

    const supabase = createClient();
    const updatePayload = {
      name: getDisplayName(authUser),
      age: toNullableInteger(formData.age),
      annual_income: toNullableFloat(formData.annual_income),
      email: toNullableString(authUser.email),
      phone_number: toNullableInteger(formData.phone_number),
      number_of_dependents: toNullableInteger(formData.number_of_dependents),
      investor_type: toNullableString(formData.investor_type),
    };

    const { data: updatedCustomer, error: updateError } = await supabase
      .from("customers")
      .update(updatePayload)
      .eq("customer_id", customerId)
      .select("*")
      .single();

    if (updateError) {
      setSaving(false);
      return { error: updateError.message || "Unable to update profile." };
    }

    setCustomer(updatedCustomer);
    setSaving(false);
    return { error: null };
  };

  const addAsset = async (payload) => {
    const customerId = authUser?.id;
    if (!customerId) {
      return { error: "You need to log in again." };
    }
    const supabase = createClient();
    const { data, error: queryError } = await supabase
      .from("customer_assets")
      .insert({
        customer_id: customerId,
        asset_value: toNullableInteger(payload.asset_value),
        current_value: toNullableFloat(payload.current_value),
      })
      .select("*")
      .single();
    if (queryError) {
      return { error: queryError.message || "Unable to add asset." };
    }
    setAssets((prev) => [data, ...prev]);
    return { error: null };
  };

  const updateAsset = async (assetId, payload) => {
    const customerId = authUser?.id;
    if (!customerId) {
      return { error: "You need to log in again." };
    }
    const supabase = createClient();
    const { data, error: queryError } = await supabase
      .from("customer_assets")
      .update({
        asset_value: toNullableInteger(payload.asset_value),
        current_value: toNullableFloat(payload.current_value),
      })
      .eq("asset_id", assetId)
      .eq("customer_id", customerId)
      .select("*")
      .single();
    if (queryError) {
      return { error: queryError.message || "Unable to update asset." };
    }
    setAssets((prev) => prev.map((asset) => (asset.asset_id === assetId ? data : asset)));
    return { error: null };
  };

  const deleteAsset = async (assetId) => {
    const customerId = authUser?.id;
    if (!customerId) {
      setError("You need to log in again.");
      return;
    }
    const supabase = createClient();
    const { error: queryError } = await supabase
      .from("customer_assets")
      .delete()
      .eq("asset_id", assetId)
      .eq("customer_id", customerId);
    if (queryError) {
      setError(queryError.message || "Unable to delete asset.");
      return;
    }
    setAssets((prev) => prev.filter((asset) => asset.asset_id !== assetId));
  };

  const addLiability = async (payload) => {
    const customerId = authUser?.id;
    if (!customerId) {
      return { error: "You need to log in again." };
    }
    const supabase = createClient();
    const { data, error: queryError } = await supabase
      .from("customer_liabilities")
      .insert({
        customer_id: customerId,
        liability_name: toNullableString(payload.liability_name),
        current_value: toNullableFloat(payload.current_value),
      })
      .select("*")
      .single();
    if (queryError) {
      return { error: queryError.message || "Unable to add liability." };
    }
    setLiabilities((prev) => [data, ...prev]);
    return { error: null };
  };

  const updateLiability = async (liabilityId, payload) => {
    const customerId = authUser?.id;
    if (!customerId) {
      return { error: "You need to log in again." };
    }
    const supabase = createClient();
    const { data, error: queryError } = await supabase
      .from("customer_liabilities")
      .update({
        liability_name: toNullableString(payload.liability_name),
        current_value: toNullableFloat(payload.current_value),
      })
      .eq("liability_id", liabilityId)
      .eq("customer_id", customerId)
      .select("*")
      .single();
    if (queryError) {
      return { error: queryError.message || "Unable to update liability." };
    }
    setLiabilities((prev) =>
      prev.map((liability) => (liability.liability_id === liabilityId ? data : liability))
    );
    return { error: null };
  };

  const deleteLiability = async (liabilityId) => {
    const customerId = authUser?.id;
    if (!customerId) {
      setError("You need to log in again.");
      return;
    }
    const supabase = createClient();
    const { error: queryError } = await supabase
      .from("customer_liabilities")
      .delete()
      .eq("liability_id", liabilityId)
      .eq("customer_id", customerId);
    if (queryError) {
      setError(queryError.message || "Unable to delete liability.");
      return;
    }
    setLiabilities((prev) => prev.filter((item) => item.liability_id !== liabilityId));
  };

  const createPortfolio = async (payload) => {
    const customerId = authUser?.id;
    if (!customerId) {
      return { error: "You need to log in again." };
    }

    const supabase = createClient();
    const { data, error: queryError } = await supabase
      .from("portfolios")
      .insert({
        customer_id: customerId,
        portfolio_name: toNullableString(payload.portfolio_name),
      })
      .select("*")
      .single();

    if (queryError) {
      return { error: queryError.message || "Unable to create portfolio." };
    }

    setPortfolios((prev) => [...prev, data]);
    setHoldingsByPortfolio((prev) => ({ ...prev, [data.portfolio_id]: [] }));
    return { error: null };
  };

  const updatePortfolio = async (portfolioId, payload) => {
    const customerId = authUser?.id;
    if (!customerId) {
      return { error: "You need to log in again." };
    }

    const supabase = createClient();
    const { data, error: queryError } = await supabase
      .from("portfolios")
      .update({
        portfolio_name: toNullableString(payload.portfolio_name),
      })
      .eq("portfolio_id", portfolioId)
      .eq("customer_id", customerId)
      .select("*")
      .single();

    if (queryError) {
      return { error: queryError.message || "Unable to update portfolio." };
    }

    setPortfolios((prev) =>
      prev.map((portfolio) => (portfolio.portfolio_id === portfolioId ? data : portfolio))
    );
    return { error: null };
  };

  const deletePortfolio = async (portfolioId) => {
    const customerId = authUser?.id;
    if (!customerId) {
      setError("You need to log in again.");
      return;
    }

    const supabase = createClient();

    const { error: holdingsDeleteError } = await supabase
      .from("portfolio_holdings")
      .delete()
      .eq("portfolio_id", portfolioId);

    if (holdingsDeleteError) {
      setError(holdingsDeleteError.message || "Unable to delete holdings.");
      return;
    }

    const { error: portfolioDeleteError } = await supabase
      .from("portfolios")
      .delete()
      .eq("portfolio_id", portfolioId)
      .eq("customer_id", customerId);

    if (portfolioDeleteError) {
      setError(portfolioDeleteError.message || "Unable to delete portfolio.");
      return;
    }

    setPortfolios((prev) => prev.filter((portfolio) => portfolio.portfolio_id !== portfolioId));
    setHoldingsByPortfolio((prev) => {
      const next = { ...prev };
      delete next[portfolioId];
      return next;
    });
  };

  const addHolding = async (portfolioId, payload) => {
    const customerId = authUser?.id;
    if (!customerId) {
      return { error: "You need to log in again." };
    }

    const supabase = createClient();
    const { data, error: queryError } = await supabase
      .from("portfolio_holdings")
      .insert({
        portfolio_id: portfolioId,
        ticker: toNullableString(payload.ticker),
        quantity: toNullableInteger(payload.quantity),
        buy_price: toNullableFloat(payload.buy_price),
        date_of_purchase: toNullableDate(payload.date_of_purchase),
      })
      .select("*")
      .single();

    if (queryError) {
      return { error: queryError.message || "Unable to add holding." };
    }

    setHoldingsByPortfolio((prev) => ({
      ...prev,
      [portfolioId]: [...(prev[portfolioId] ?? []), data],
    }));
    return { error: null };
  };

  const updateHolding = async (holdingId, payload) => {
    const supabase = createClient();
    const { data, error: queryError } = await supabase
      .from("portfolio_holdings")
      .update({
        quantity: toNullableInteger(payload.quantity),
        buy_price: toNullableFloat(payload.buy_price),
      })
      .eq("holding_id", holdingId)
      .select("*")
      .single();

    if (queryError) {
      return { error: queryError.message || "Unable to update holding." };
    }

    setHoldingsByPortfolio((prev) => {
      const next = { ...prev };
      const portfolioId = data.portfolio_id;
      next[portfolioId] = (next[portfolioId] ?? []).map((holding) =>
        holding.holding_id === holdingId ? data : holding
      );
      return next;
    });
    return { error: null };
  };

  const deleteHolding = async (holdingId, portfolioId) => {
    const supabase = createClient();
    const { error: queryError } = await supabase
      .from("portfolio_holdings")
      .delete()
      .eq("holding_id", holdingId)
      .eq("portfolio_id", portfolioId);

    if (queryError) {
      setError(queryError.message || "Unable to delete holding.");
      return;
    }

    setHoldingsByPortfolio((prev) => ({
      ...prev,
      [portfolioId]: (prev[portfolioId] ?? []).filter((holding) => holding.holding_id !== holdingId),
    }));
  };

  const totalAssets = assets.reduce((acc, asset) => acc + Number(asset.current_value || 0), 0);
  const totalLiabilities = liabilities.reduce((acc, item) => acc + Number(item.current_value || 0), 0);
  const netWorth = totalAssets - totalLiabilities;

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-900 dark:text-zinc-100">
        <Header />
        <main className="container mx-auto px-6 pb-16 pt-28">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 text-sm text-zinc-600 shadow-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
            Loading profile...
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-900 dark:text-zinc-100">
      <Header />
      <main className="container mx-auto px-6 pb-16 pt-28">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Your Profile</h1>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            Complete financial profile dashboard.
          </p>
        </div>

        {error ? (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        ) : null}

        <section className="mb-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Total Assets</p>
            <p className="mt-2 text-2xl font-semibold">{formatCurrency(totalAssets)}</p>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Total Liabilities</p>
            <p className="mt-2 text-2xl font-semibold">{formatCurrency(totalLiabilities)}</p>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Net Worth</p>
            <p className="mt-2 text-2xl font-semibold">{formatCurrency(netWorth)}</p>
          </div>
        </section>

        <div className="mb-6 flex flex-wrap gap-2">
          {[
            ["basic", "Basic Information"],
            ["assets", "Assets"],
            ["liabilities", "Liabilities"],
            ["portfolios", "Portfolio"],
            ["analysis", "Analysis History"],
          ].map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                activeTab === key
                  ? "bg-blue-600 text-white"
                  : "border border-zinc-300 text-zinc-700 hover:bg-zinc-100 dark:border-zinc-600 dark:text-zinc-200 dark:hover:bg-zinc-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="space-y-6">
          {activeTab === "basic" ? (
            <BasicInfo customer={customer} authUser={authUser} onSave={saveBasicInfo} saving={saving} />
          ) : null}

          {activeTab === "assets" ? (
            <AssetsSection
              assets={assets}
              totalAssets={formatCurrency(totalAssets)}
              onAdd={addAsset}
              onUpdate={updateAsset}
              onDelete={deleteAsset}
            />
          ) : null}

          {activeTab === "liabilities" ? (
            <LiabilitiesSection
              liabilities={liabilities}
              totalLiabilities={formatCurrency(totalLiabilities)}
              onAdd={addLiability}
              onUpdate={updateLiability}
              onDelete={deleteLiability}
            />
          ) : null}

          {activeTab === "portfolios" ? (
            <PortfolioSection
              portfolios={portfolios}
              holdingsByPortfolio={holdingsByPortfolio}
              onCreatePortfolio={createPortfolio}
              onUpdatePortfolio={updatePortfolio}
              onDeletePortfolio={deletePortfolio}
              onAddHolding={addHolding}
              onUpdateHolding={updateHolding}
              onDeleteHolding={deleteHolding}
            />
          ) : null}

          {activeTab === "analysis" ? (
            <AnalysisHistory analysisHistory={analysisHistory} />
          ) : null}
        </div>
      </main>
    </div>
  );
}
