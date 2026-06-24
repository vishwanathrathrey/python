import { FormEvent, useEffect, useMemo, useState } from 'react';
import { fetchHealth, fetchMetrics, predictRisk, type MetricsPayload, type PredictResponse } from './api';

type FeatureField = {
  key: string;
  label: string;
  placeholder: string;
  step?: string;
  inputType?: 'number' | 'date' | 'select';
};

const FEATURE_FIELDS: FeatureField[] = [
  { key: 'fm_amt_income_total', label: 'Income', placeholder: '180000', step: '1000' },
  { key: 'fm_amt_credit', label: 'Loan amount', placeholder: '450000', step: '1000' },
  { key: 'fm_days_birth', label: 'Date of birth', placeholder: '1993-01-01', inputType: 'date' },
  { key: 'fm_ext_source_2', label: 'Credit score 2', placeholder: '0.42', step: '0.01' },
  { key: 'fm_ext_source_3', label: 'Credit score 3', placeholder: '0.58', step: '0.01' },
  { key: 'fm_cnt_fam_members', label: 'Family size', placeholder: '2', step: '1' },
  { key: 'fm_region_rating_client', label: 'Area risk score', placeholder: '2', step: '1' },
  { key: 'fm_days_employed', label: 'Employment start date', placeholder: '2017-05-01', inputType: 'date' },
  { key: 'fm_amt_annuity', label: 'Monthly payment', placeholder: '24500', step: '100' },
  { key: 'fm_amt_goods_price', label: 'Item price', placeholder: '540000', step: '1000' },
  { key: 'fm_days_registration', label: 'Address registration date', placeholder: '2019-03-01', inputType: 'date' },
  { key: 'fm_days_id_publish', label: 'ID issue date', placeholder: '2018-10-01', inputType: 'date' },
  { key: 'fm_flag_own_car', label: 'Owns car', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_own_realty', label: 'Owns property', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_phone', label: 'Has phone', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_work_phone', label: 'Has work phone', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_emp_phone', label: 'Employer phone', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_email', label: 'Has email', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_mobil', label: 'Has mobile', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_cont_mobile', label: 'Can be reached on mobile', placeholder: '1', inputType: 'select' },
  { key: 'fm_name_income_type', label: 'Income type', placeholder: '1', step: '1' },
  { key: 'fm_name_education_type', label: 'Education level', placeholder: '1', step: '1' },
  { key: 'fm_name_family_status', label: 'Family status', placeholder: '1', step: '1' },
  { key: 'fm_name_housing_type', label: 'Housing type', placeholder: '1', step: '1' },
  { key: 'fm_name_contract_type', label: 'Contract type', placeholder: '1', step: '1' },
  { key: 'fm_occupation_type', label: 'Job type', placeholder: '1', step: '1' },
  { key: 'fm_region_rating_client_w_city', label: 'Area score with city', placeholder: '2', step: '1' },
  { key: 'fm_name_type_suite', label: 'Home type', placeholder: '1', step: '1' },
  { key: 'fm_flag_document_3', label: 'Document 3 provided?', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_document_6', label: 'Document 6 provided?', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_document_8', label: 'Document 8 provided?', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_document_15', label: 'Document 15 provided?', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_document_18', label: 'Document 18 provided?', placeholder: '1', inputType: 'select' },
  { key: 'fm_flag_document_21', label: 'Document 21 provided?', placeholder: '1', inputType: 'select' },
];

function describeField(field: FeatureField) {
  if (field.key === 'fm_days_birth') {
    return 'Choose the applicant date of birth.';
  }

  if (field.key === 'fm_days_employed') {
    return 'Choose the date the applicant started their current job.';
  }

  if (field.key === 'fm_days_registration') {
    return 'Choose the date the applicant registered or started living at this address.';
  }

  if (field.key === 'fm_days_id_publish') {
    return 'Choose the date the ID document was issued.';
  }

  if (field.key.startsWith('fm_amt_')) {
    return `Enter a money value in numbers only. Example: ${field.placeholder}.`;
  }

  if (field.key.startsWith('fm_days_')) {
    return 'Choose a date for this event.';
  }

  if (field.key.startsWith('fm_ext_source_')) {
    return `Enter a score between 0 and 1. Example: ${field.placeholder}.`;
  }

  if (field.key.startsWith('fm_flag_')) {
    return 'Choose yes or no from the dropdown. Yes is stored as 1 and no is stored as 0.';
  }

  if (field.key.startsWith('fm_name_') || field.key.includes('occupation') || field.key.includes('region') || field.key.includes('suite')) {
    return `Enter the numeric category code if you know it. Otherwise leave it blank. Example: ${field.placeholder}.`;
  }

  return `Enter a number. Example: ${field.placeholder}.`;
}

const MS_PER_DAY = 24 * 60 * 60 * 1000;

function getTodayStart() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today;
}

function dateStringFromNegativeDays(days: number) {
  const dob = new Date(getTodayStart().getTime() + days * MS_PER_DAY);
  return dob.toISOString().slice(0, 10);
}

function calculateNegativeDaysFromDOB(dobValue: string) {
  const dob = new Date(`${dobValue}T00:00:00`);
  if (Number.isNaN(dob.getTime())) {
    throw new Error('Please enter a valid date of birth.');
  }

  const diffDays = Math.floor((getTodayStart().getTime() - dob.getTime()) / MS_PER_DAY);
  if (diffDays < 0) {
    throw new Error('Date of birth cannot be in the future.');
  }

  return -diffDays;
}

const SAMPLE_PRESETS: Record<string, Record<string, number | string>> = {
  balanced: {
    fm_amt_income_total: 180000,
    fm_amt_credit: 450000,
    fm_days_birth: dateStringFromNegativeDays(-12000),
    fm_ext_source_2: 0.42,
    fm_ext_source_3: 0.58,
    fm_cnt_fam_members: 2,
    fm_region_rating_client: 2,
    fm_days_employed: dateStringFromNegativeDays(-2500),
    fm_amt_annuity: 24500,
    fm_amt_goods_price: 540000,
    fm_days_registration: dateStringFromNegativeDays(-3200),
    fm_days_id_publish: dateStringFromNegativeDays(-4100),
    fm_flag_own_car: 1,
    fm_flag_own_realty: 1,
    fm_flag_phone: 1,
    fm_flag_work_phone: 1,
    fm_flag_emp_phone: 1,
    fm_flag_email: 1,
    fm_flag_mobil: 1,
    fm_flag_cont_mobile: 1,
    fm_name_income_type: 1,
    fm_name_education_type: 1,
    fm_name_family_status: 1,
    fm_name_housing_type: 1,
    fm_name_contract_type: 1,
    fm_occupation_type: 1,
    fm_region_rating_client_w_city: 2,
    fm_name_type_suite: 1,
    fm_flag_document_3: 1,
    fm_flag_document_6: 1,
    fm_flag_document_8: 1,
    fm_flag_document_15: 1,
    fm_flag_document_18: 1,
    fm_flag_document_21: 1,
  },
  cautious: {
    fm_amt_income_total: 320000,
    fm_amt_credit: 180000,
    fm_days_birth: dateStringFromNegativeDays(-14500),
    fm_ext_source_2: 0.72,
    fm_ext_source_3: 0.74,
    fm_cnt_fam_members: 1,
    fm_region_rating_client: 3,
    fm_days_employed: dateStringFromNegativeDays(-6400),
    fm_amt_annuity: 12000,
    fm_amt_goods_price: 260000,
    fm_days_registration: dateStringFromNegativeDays(-5400),
    fm_days_id_publish: dateStringFromNegativeDays(-6200),
    fm_flag_own_car: 0,
    fm_flag_own_realty: 1,
    fm_flag_phone: 1,
    fm_flag_work_phone: 1,
    fm_flag_emp_phone: 1,
    fm_flag_email: 1,
    fm_flag_mobil: 1,
    fm_flag_cont_mobile: 1,
    fm_name_income_type: 2,
    fm_name_education_type: 2,
    fm_name_family_status: 2,
    fm_name_housing_type: 1,
    fm_name_contract_type: 1,
    fm_occupation_type: 2,
    fm_region_rating_client_w_city: 3,
    fm_name_type_suite: 1,
    fm_flag_document_3: 1,
    fm_flag_document_6: 1,
    fm_flag_document_8: 1,
    fm_flag_document_15: 1,
    fm_flag_document_18: 1,
    fm_flag_document_21: 1,
  },
  stressed: {
    fm_amt_income_total: 96000,
    fm_amt_credit: 680000,
    fm_days_birth: dateStringFromNegativeDays(-9800),
    fm_ext_source_2: 0.16,
    fm_ext_source_3: 0.22,
    fm_cnt_fam_members: 4,
    fm_region_rating_client: 3,
    fm_days_employed: dateStringFromNegativeDays(-900),
    fm_amt_annuity: 48000,
    fm_amt_goods_price: 780000,
    fm_days_registration: dateStringFromNegativeDays(-1200),
    fm_days_id_publish: dateStringFromNegativeDays(-1100),
    fm_flag_own_car: 0,
    fm_flag_own_realty: 0,
    fm_flag_phone: 1,
    fm_flag_work_phone: 0,
    fm_flag_emp_phone: 0,
    fm_flag_email: 0,
    fm_flag_mobil: 1,
    fm_flag_cont_mobile: 1,
    fm_name_income_type: 3,
    fm_name_education_type: 3,
    fm_name_family_status: 3,
    fm_name_housing_type: 2,
    fm_name_contract_type: 2,
    fm_occupation_type: 3,
    fm_region_rating_client_w_city: 3,
    fm_name_type_suite: 2,
    fm_flag_document_3: 0,
    fm_flag_document_6: 0,
    fm_flag_document_8: 0,
    fm_flag_document_15: 0,
    fm_flag_document_18: 0,
    fm_flag_document_21: 0,
  },
};

const INITIAL_VALUES = FEATURE_FIELDS.reduce<Record<string, string>>((accumulator, field) => {
  accumulator[field.key] = '';
  return accumulator;
}, {});

function formatPercent(value: number) {
  return `${(value * 100).toFixed(3)}%`;
}

function riskTone(riskLevel: PredictResponse['risk_level']) {
  if (riskLevel === 'low') return 'safe';
  if (riskLevel === 'medium') return 'watch';
  return 'alert';
}

export default function App() {
  const [values, setValues] = useState<Record<string, string>>(INITIAL_VALUES);
  const [health, setHealth] = useState<{ status: string; model_loaded: boolean; feature_count: number } | null>(null);
  const [metrics, setMetrics] = useState<MetricsPayload | null>(null);
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    Promise.all([fetchHealth(), fetchMetrics()])
      .then(([healthResponse, metricsResponse]) => {
        if (cancelled) return;
        setHealth(healthResponse);
        setMetrics(metricsResponse);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setApiError(error instanceof Error ? error.message : 'Unable to load API status');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const topMetrics = useMemo(() => {
    if (!metrics) return null;

    const selectedModel = metrics.selected_model;
    const modelMetrics = metrics.metrics[selectedModel];
    if (!modelMetrics) return null;

    return {
      selectedModel,
      rocAuc: modelMetrics.roc_auc,
      recall: modelMetrics.recall,
      accuracy: modelMetrics.accuracy,
    };
  }, [metrics]);

  const filledCount = useMemo(() => Object.values(values).filter((value) => value.trim() !== '').length, [values]);

  const dobDaysPreview = useMemo(() => {
    if (!values.fm_days_birth) return null;

    try {
      return calculateNegativeDaysFromDOB(values.fm_days_birth);
    } catch {
      return null;
    }
  }, [values.fm_days_birth]);

  function updateValue(key: string, value: string) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function loadPreset(name: keyof typeof SAMPLE_PRESETS) {
    const preset = SAMPLE_PRESETS[name];
    const nextValues = { ...INITIAL_VALUES };
    for (const [key, value] of Object.entries(preset)) {
      nextValues[key] = String(value);
    }
    setValues(nextValues);
    setPrediction(null);
    setApiError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setApiError(null);

    try {
      const features = Object.fromEntries(
        Object.entries(values)
          .filter(([, rawValue]) => rawValue.trim() !== '')
          .map(([key, rawValue]) => {
            if (key === 'fm_days_birth') {
              return [key, calculateNegativeDaysFromDOB(rawValue)];
            }

            return [key, Number(rawValue)];
          }),
      );

      const response = await predictRisk(features);
      setPrediction(response);
    } catch (error: unknown) {
      setApiError(error instanceof Error ? error.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  }

  const riskMessage = prediction ? `${prediction.risk_level.toUpperCase()} RISK` : 'Awaiting score';

  return (
    <div className="shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <main className="dashboard">
        <section className="hero">
          <div>
            <p className="eyebrow">Credit Risk Prediction System</p>
            <h1>Score loan applications with a FastAPI-backed model.</h1>
            <p className="hero-copy">
              Enter a few simple applicant details, send them to the API, and get a default probability and risk band
              in one response.
            </p>
          </div>

          <div className={`status-card ${prediction ? riskTone(prediction.risk_level) : 'neutral'}`}>
            <div className="status-pill">{riskMessage}</div>
            <div className="probability">{prediction ? formatPercent(prediction.default_probability) : '--'}</div>
            <div className="status-meta">
              <span>{prediction?.selected_model ?? topMetrics?.selectedModel ?? 'model pending'}</span>
              <span>{health?.status === 'ok' ? 'API online' : 'API loading'}</span>
            </div>
          </div>
        </section>

        <section className="metrics-row">
          <article className="metric-card">
            <span className="metric-label">API health</span>
            <strong>{health?.model_loaded ? 'Ready' : 'Checking'}</strong>
            <p>{health ? `${health.feature_count.toLocaleString()} training features discovered` : 'Waiting on backend'}</p>
          </article>
          <article className="metric-card">
            <span className="metric-label">Selected model</span>
            <strong>{topMetrics?.selectedModel ?? 'Loading'}</strong>
            <p>{topMetrics ? `ROC-AUC ${topMetrics.rocAuc.toFixed(3)}` : 'Fetching metrics bundle'}</p>
          </article>
          <article className="metric-card">
            <span className="metric-label">Recall</span>
            <strong>{topMetrics ? topMetrics.recall.toFixed(3) : '--'}</strong>
            <p>{topMetrics ? `Accuracy ${topMetrics.accuracy.toFixed(3)}` : 'Available after metrics load'}</p>
          </article>
          <article className="metric-card">
            <span className="metric-label">Filled inputs</span>
            <strong>{filledCount}</strong>
            <p>Showing a curated subset of the trained feature space.</p>
          </article>
        </section>

        <section className="content-grid">
          <article className="panel form-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Applicant profile</p>
                <h2>Enter the applicant details you know</h2>
              </div>
              <div className="preset-group">
                <button className="preset-button preset-balanced" type="button" onClick={() => loadPreset('balanced')}>
                  Balanced sample
                </button>
                <button className="preset-button preset-cautious" type="button" onClick={() => loadPreset('cautious')}>
                  Cautious sample
                </button>
                <button className="preset-button preset-stressed" type="button" onClick={() => loadPreset('stressed')}>
                  Stressed sample
                </button>
              </div>
            </div>

            <div className="form-note">
              <p>
                Fill in the details you know. Leave unknown fields blank. The model will still make a prediction.
              </p>
              <p>Use the sample buttons to auto-fill a balanced, lower-risk, or higher-risk example profile.</p>
              <ul>
                <li>Amounts: type the money value in numbers only.</li>
                <li>Date fields: choose the date for the event shown on each field.</li>
                <li>Yes/no fields: choose yes or no from the dropdown. Yes is 1 and no is 0.</li>
                <li>Category fields: enter the number code if you know it, otherwise leave blank.</li>
              </ul>
            </div>

            <form onSubmit={handleSubmit} className="feature-form">
              {FEATURE_FIELDS.map((field) => (
                <label key={field.key} className="field-card">
                  <span className="field-label">{field.label}</span>
                  {field.inputType === 'select' ? (
                    <select value={values[field.key]} onChange={(event) => updateValue(field.key, event.target.value)}>
                      <option value="">Select yes or no</option>
                      <option value="1">Yes</option>
                      <option value="0">No</option>
                    </select>
                  ) : (
                    <input
                      type={field.inputType ?? 'number'}
                      inputMode={field.inputType === 'date' ? undefined : 'decimal'}
                      step={field.step ?? 'any'}
                      placeholder={field.placeholder}
                      value={values[field.key]}
                      onChange={(event) => updateValue(field.key, event.target.value)}
                    />
                  )}
                  <small>{describeField(field)}</small>
                </label>
              ))}

              <div className="form-actions">
                <button className="primary-button" type="submit" disabled={loading}>
                  {loading ? 'Scoring...' : 'Predict default risk'}
                </button>
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => {
                    setValues(INITIAL_VALUES);
                    setPrediction(null);
                    setApiError(null);
                  }}
                >
                  Clear form
                </button>
              </div>
            </form>

            {apiError ? <div className="error-banner">{apiError}</div> : null}
          </article>

          <article className="panel result-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Prediction output</p>
                <h2>Probability and risk band</h2>
              </div>
            </div>

            <div className={`result-card ${prediction ? riskTone(prediction.risk_level) : 'neutral'}`}>
              <span className="result-label">Default probability</span>
              <strong>{prediction ? formatPercent(prediction.default_probability) : '--'}</strong>
              <p>
                {prediction
                  ? `${prediction.selected_model} scored the applicant with ${prediction.missing_feature_count} missing features auto-filled by the model pipeline.`
                  : 'Submit an application profile to generate a score.'}
              </p>
            </div>

            <div className="insight-stack">
              <div className="insight-item">
                <span>Risk level</span>
                <strong>{prediction?.risk_level ?? 'n/a'}</strong>
              </div>
              <div className="insight-item">
                <span>Model</span>
                <strong>{prediction?.selected_model ?? 'n/a'}</strong>
              </div>
              <div className="insight-item">
                <span>Missing fields</span>
                <strong>{prediction ? prediction.missing_feature_count : 'n/a'}</strong>
              </div>
            </div>

            <div className="note-card">
              <strong>How it works</strong>
              <p>
                The frontend sends only the fields you enter. The API aligns them to the trained schema, fills the rest
                as missing values, and lets the model pipeline handle imputation.
              </p>
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}
