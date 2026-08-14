<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="budget-header">
        <label for="budget-slider">{{ t('restocking.budgetLabel') }}</label>
        <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
      <input
        id="budget-slider"
        type="range"
        min="0"
        max="10000"
        step="100"
        v-model.number="budget"
        class="budget-slider"
      />
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="recommendations.length === 0" class="empty-state">
        {{ t('restocking.noRecommendations') }}
      </div>
      <div v-else>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.quantity }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ item.line_total.toLocaleString() }}</td>
                <td>{{ t('restocking.leadTimeDays', { days: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="summary-strip">
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.totalCost') }}</span>
            <span class="summary-value">{{ currencySymbol }}{{ totalCost.toLocaleString() }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.remainingBudget') }}</span>
            <span class="summary-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</span>
          </div>
        </div>

        <div v-if="submitSuccess" class="success-banner">
          {{ t('restocking.orderSubmitted') }}
        </div>
        <div v-if="submitError" class="error">
          {{ t('restocking.orderSubmitError') }}: {{ submitError }}
        </div>

        <button
          class="place-order-btn"
          :disabled="budget <= 0 || recommendations.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(1000)
    const recommendations = ref([])
    const loading = ref(false)
    const error = ref(null)

    const submitting = ref(false)
    const submitSuccess = ref(false)
    const submitError = ref(null)

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.line_total, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - totalCost.value
    })

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendations.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch(budget, loadRecommendations)

    const placeOrder = async () => {
      try {
        submitting.value = true
        submitSuccess.value = false
        submitError.value = null
        await api.createRestockingOrder({
          budget: budget.value,
          items: recommendations.value
        })
        submitSuccess.value = true
      } catch (err) {
        submitError.value = err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      currencySymbol,
      budget,
      recommendations,
      loading,
      error,
      totalCost,
      remainingBudget,
      submitting,
      submitSuccess,
      submitError,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.budget-header label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  margin-top: -7px;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.budget-slider::-moz-range-progress {
  height: 6px;
  border-radius: 3px;
  background: #2563eb;
}

.budget-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.budget-slider::-moz-range-thumb:hover {
  transform: scale(1.1);
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.summary-strip {
  display: flex;
  gap: 2rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1.25rem;
  font-size: 0.938rem;
}

.place-order-btn {
  margin-top: 1.25rem;
  padding: 0.75rem 1.75rem;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
