<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Budget-driven restocking recommendations based on demand forecasts and current inventory levels.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>

      <!-- Section 1: Budget Slider -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Budget Allocation</h3>
        </div>
        <div class="budget-section">
          <div class="budget-slider-row">
            <label class="budget-label" for="budget-slider">Available Budget</label>
            <span class="budget-display">{{ formatCurrency(budget) }}</span>
          </div>
          <input
            id="budget-slider"
            type="range"
            min="0"
            max="1000000"
            step="10000"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-markers">
            <span>$0</span>
            <span>$250K</span>
            <span>$500K</span>
            <span>$750K</span>
            <span>$1M</span>
          </div>
          <div class="budget-stats">
            <div class="budget-stat">
              <span class="budget-stat-label">Budget Used</span>
              <span class="budget-stat-value used">{{ formatCurrency(budgetUsed) }}</span>
            </div>
            <div class="budget-stat">
              <span class="budget-stat-label">Remaining</span>
              <span class="budget-stat-value" :class="budgetRemaining < 0 ? 'over' : 'remaining'">
                {{ formatCurrency(budgetRemaining) }}
              </span>
            </div>
            <div class="budget-stat">
              <span class="budget-stat-label">Utilization</span>
              <span class="budget-stat-value">
                {{ budget > 0 ? ((budgetUsed / budget) * 100).toFixed(1) : '0.0' }}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Section 2: Restocking Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Restocking Recommendations</h3>
          <span class="card-subtitle">Sorted by trend and cost - greedy budget allocation</span>
        </div>

        <div v-if="budget === 0" class="empty-state">
          Set a budget above to see restocking recommendations.
        </div>
        <div v-else-if="recommendedItems.length === 0" class="empty-state">
          Increase budget to see recommendations. Minimum required: {{ formatCurrency(cheapestItemCost) }}.
        </div>
        <div v-else>
          <div class="table-container">
            <table class="restocking-table">
              <thead>
                <tr>
                  <th>Item Name</th>
                  <th>SKU</th>
                  <th>Trend</th>
                  <th class="col-num">Qty to Order</th>
                  <th class="col-num">Unit Cost</th>
                  <th class="col-num">Estimated Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendedItems" :key="item.sku">
                  <td><strong>{{ item.name }}</strong></td>
                  <td class="col-sku">{{ item.sku }}</td>
                  <td>
                    <span :class="['badge', item.trend]">{{ item.trend }}</span>
                  </td>
                  <td class="col-num">{{ item.quantity_to_order.toLocaleString() }}</td>
                  <td class="col-num">{{ formatCurrency(item.unit_cost) }}</td>
                  <td class="col-num"><strong>{{ formatCurrency(item.estimated_cost) }}</strong></td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="summary-row">
                  <td colspan="3">
                    <strong>Total: {{ recommendedItems.length }} items</strong>
                  </td>
                  <td class="col-num">
                    <strong>{{ totalUnits.toLocaleString() }}</strong>
                  </td>
                  <td></td>
                  <td class="col-num">
                    <strong>{{ formatCurrency(budgetUsed) }}</strong>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      <!-- Section 3: Place Order -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Place Order</h3>
        </div>
        <div class="order-section">
          <div v-if="orderSuccess" class="success-message">
            Order <strong>{{ orderSuccess.order_number }}</strong> placed successfully.
            Expected delivery: <strong>{{ orderSuccess.expected_delivery }}</strong>
          </div>

          <div class="order-summary" v-if="recommendedItems.length > 0">
            <p>
              Ready to submit <strong>{{ recommendedItems.length }} item(s)</strong>
              totaling <strong>{{ formatCurrency(budgetUsed) }}</strong>.
            </p>
          </div>
          <div class="order-summary" v-else>
            <p class="muted">No items selected. Adjust the budget slider to include items.</p>
          </div>

          <button
            class="btn-place-order"
            :disabled="recommendedItems.length === 0 || placingOrder"
            @click="placeOrder"
          >
            {{ placingOrder ? 'Placing Order...' : 'Place Order' }}
          </button>

          <div v-if="orderError" class="error">{{ orderError }}</div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)

    const demandForecasts = ref([])
    const inventoryItems = ref([])

    const budget = ref(200000)
    const placingOrder = ref(false)
    const orderSuccess = ref(null)
    const orderError = ref(null)

    // All candidate items (quantity_to_order > 0), sorted
    const candidateItems = computed(() => {
      const inventoryMap = {}
      for (const inv of inventoryItems.value) {
        inventoryMap[inv.sku] = inv
      }

      const items = []
      for (const forecast of demandForecasts.value) {
        const inv = inventoryMap[forecast.item_sku]
        if (!inv) continue

        const quantity_to_order = Math.max(forecast.forecasted_demand - inv.quantity_on_hand, 0)
        if (quantity_to_order === 0) continue

        const estimated_cost = quantity_to_order * inv.unit_cost

        items.push({
          sku: forecast.item_sku,
          name: forecast.item_name,
          trend: forecast.trend,
          quantity_to_order,
          unit_cost: inv.unit_cost,
          estimated_cost
        })
      }

      items.sort((a, b) => {
        const trendDiff = (TREND_ORDER[a.trend] ?? 99) - (TREND_ORDER[b.trend] ?? 99)
        if (trendDiff !== 0) return trendDiff
        return b.estimated_cost - a.estimated_cost
      })

      return items
    })

    // Greedy selection within budget
    const recommendedItems = computed(() => {
      const selected = []
      let remaining = budget.value
      for (const item of candidateItems.value) {
        if (item.estimated_cost <= remaining) {
          selected.push(item)
          remaining -= item.estimated_cost
        }
      }
      return selected
    })

    const budgetUsed = computed(() =>
      recommendedItems.value.reduce((sum, item) => sum + item.estimated_cost, 0)
    )

    const budgetRemaining = computed(() => budget.value - budgetUsed.value)

    const totalUnits = computed(() =>
      recommendedItems.value.reduce((sum, item) => sum + item.quantity_to_order, 0)
    )

    const cheapestItemCost = computed(() => {
      if (candidateItems.value.length === 0) return 0
      return Math.min(...candidateItems.value.map(i => i.estimated_cost))
    })

    const formatCurrency = (value) => {
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
    }

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        demandForecasts.value = forecasts
        inventoryItems.value = inventory
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendedItems.value.length === 0 || placingOrder.value) return

      placingOrder.value = true
      orderError.value = null
      orderSuccess.value = null

      try {
        const payload = {
          items: recommendedItems.value.map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: item.quantity_to_order,
            unit_cost: item.unit_cost
          })),
          budget_used: budgetUsed.value
        }
        const result = await api.createRestockingOrder(payload)
        orderSuccess.value = result

        // Clear success message after 5 seconds then reload
        setTimeout(() => {
          orderSuccess.value = null
        }, 5000)
      } catch (err) {
        orderError.value = 'Failed to place order: ' + err.message
        console.error(err)
      } finally {
        placingOrder.value = false
      }
    }

    onMounted(loadData)

    return {
      loading,
      error,
      budget,
      recommendedItems,
      candidateItems,
      budgetUsed,
      budgetRemaining,
      totalUnits,
      cheapestItemCost,
      placingOrder,
      orderSuccess,
      orderError,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

/* Budget slider */
.budget-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-slider-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-display {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.budget-markers {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
}

.budget-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.budget-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.budget-stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.budget-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-stat-value.used {
  color: #2563eb;
}

.budget-stat-value.remaining {
  color: #059669;
}

.budget-stat-value.over {
  color: #dc2626;
}

/* Table */
.restocking-table {
  width: 100%;
  border-collapse: collapse;
}

.col-num {
  text-align: right;
  width: 140px;
}

.col-sku {
  font-family: 'Courier New', monospace;
  font-size: 0.813rem;
  color: #64748b;
}

tfoot .summary-row td {
  background: #f8fafc;
  border-top: 2px solid #e2e8f0;
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
  color: #0f172a;
}

/* Card subtitle */
.card-subtitle {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 400;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-size: 0.938rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}

/* Order section */
.order-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.order-summary p {
  font-size: 0.938rem;
  color: #334155;
}

.order-summary p.muted {
  color: #94a3b8;
}

.btn-place-order {
  align-self: flex-start;
  padding: 0.75rem 2rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-place-order:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-place-order:disabled {
  background: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
}

.success-message {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  font-size: 0.938rem;
}
</style>
