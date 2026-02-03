import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'
import { useAuthStore } from './auth'

export const useTicketsStore = defineStore('tickets', () => {
  // State
  const tickets = ref([])
  const currentTicket = ref(null)
  const stats = ref({
    total: 0,
    new: 0,
    open: 0,
    pending: 0,
    resolved: 0,
    closed: 0,
    sla_breached: 0,
    by_priority: {},
    by_type: {}
  })
  const loading = ref(false)
  const error = ref(null)

  // Filters
  const filters = ref({
    status: null,
    priority: null,
    ticket_type: null,
    category: null,
    search: '',
    my_tickets: false
  })

  // ==================== Optimistic UI Helpers ====================

  // Update stats optimistically based on status change
  function updateStatsForStatusChange(oldStatus, newStatus, count = 1) {
    if (oldStatus && stats.value[oldStatus] !== undefined) {
      stats.value[oldStatus] = Math.max(0, stats.value[oldStatus] - count)
    }
    if (newStatus && stats.value[newStatus] !== undefined) {
      stats.value[newStatus] += count
    }
  }

  // Update stats when a new ticket is created
  function incrementStatsForNewTicket(status = 'new', priority = 'medium', ticketType = 'incident') {
    stats.value.total += 1
    if (stats.value[status] !== undefined) {
      stats.value[status] += 1
    }
    if (stats.value.by_priority && stats.value.by_priority[priority] !== undefined) {
      stats.value.by_priority[priority] += 1
    } else if (stats.value.by_priority) {
      stats.value.by_priority[priority] = 1
    }
    if (stats.value.by_type && stats.value.by_type[ticketType] !== undefined) {
      stats.value.by_type[ticketType] += 1
    } else if (stats.value.by_type) {
      stats.value.by_type[ticketType] = 1
    }
  }

  // Update stats when a ticket is deleted
  function decrementStatsForDeletedTicket(ticket) {
    stats.value.total = Math.max(0, stats.value.total - 1)
    if (ticket.status && stats.value[ticket.status] !== undefined) {
      stats.value[ticket.status] = Math.max(0, stats.value[ticket.status] - 1)
    }
    if (ticket.priority && stats.value.by_priority && stats.value.by_priority[ticket.priority] !== undefined) {
      stats.value.by_priority[ticket.priority] = Math.max(0, stats.value.by_priority[ticket.priority] - 1)
    }
    if (ticket.ticket_type && stats.value.by_type && stats.value.by_type[ticket.ticket_type] !== undefined) {
      stats.value.by_type[ticket.ticket_type] = Math.max(0, stats.value.by_type[ticket.ticket_type] - 1)
    }
    if (ticket.sla_breached && stats.value.sla_breached > 0) {
      stats.value.sla_breached -= 1
    }
  }

  // ==================== Getters ====================

  const openTickets = computed(() =>
    tickets.value.filter(t => ['new', 'open', 'pending'].includes(t.status))
  )

  const myTickets = computed(() => {
    // Use auth store for reactive user data instead of localStorage
    const authStore = useAuthStore()
    const userId = authStore.user?.id
    if (!userId) return []
    return tickets.value.filter(t =>
      t.assigned_to_id === userId || t.requester_id === userId
    )
  })

  // Actions
  async function fetchTickets(options = {}) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()

      // Apply filters
      if (filters.value.status) params.append('status', filters.value.status)
      if (filters.value.priority) params.append('priority', filters.value.priority)
      if (filters.value.ticket_type) params.append('ticket_type', filters.value.ticket_type)
      if (filters.value.category) params.append('category', filters.value.category)
      if (filters.value.search) params.append('search', filters.value.search)
      if (filters.value.my_tickets) params.append('my_tickets', 'true')

      // Pagination
      if (options.skip) params.append('skip', options.skip)
      if (options.limit) params.append('limit', options.limit)

      const response = await api.get(`/tickets/?${params}`)
      tickets.value = response.data.items || response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch tickets'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTicketStats() {
    try {
      const response = await api.get('/tickets/stats')
      stats.value = response.data
      return response.data
    } catch (err) {
      // Error handled by API interceptor
      throw err
    }
  }

  async function fetchTicket(id) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/tickets/${id}`)
      currentTicket.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch ticket'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createTicket(ticketData) {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/tickets/', ticketData)
      tickets.value.unshift(response.data)
      // Optimistic stats update
      incrementStatsForNewTicket(
        response.data.status || 'new',
        response.data.priority || 'medium',
        response.data.ticket_type || 'incident'
      )
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create ticket'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateTicket(id, ticketData) {
    loading.value = true
    error.value = null
    try {
      const response = await api.put(`/tickets/${id}`, ticketData)
      const index = tickets.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tickets.value[index] = { ...tickets.value[index], ...response.data }
      }
      if (currentTicket.value?.id === id) {
        currentTicket.value = { ...currentTicket.value, ...response.data }
      }
      await fetchTicketStats()
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update ticket'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteTicket(id) {
    loading.value = true
    error.value = null

    // Store for optimistic update and potential rollback
    const ticketIndex = tickets.value.findIndex(t => t.id === id)
    const removedTicket = ticketIndex !== -1 ? { ...tickets.value[ticketIndex] } : null

    // Optimistic removal
    if (ticketIndex !== -1) {
      tickets.value.splice(ticketIndex, 1)
    }

    try {
      await api.delete(`/tickets/${id}`)
      if (currentTicket.value?.id === id) {
        currentTicket.value = null
      }
      // Optimistic stats update
      if (removedTicket) {
        decrementStatsForDeletedTicket(removedTicket)
      }
    } catch (err) {
      // Rollback on error
      if (removedTicket && ticketIndex !== -1) {
        tickets.value.splice(ticketIndex, 0, removedTicket)
      }
      error.value = err.response?.data?.detail || 'Failed to delete ticket'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addComment(ticketId, commentData) {
    try {
      const response = await api.post(`/tickets/${ticketId}/comments`, commentData)
      if (currentTicket.value?.id === ticketId) {
        currentTicket.value.comments.push(response.data)
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to add comment'
      throw err
    }
  }

  async function assignTicket(ticketId, userId) {
    try {
      const response = await api.post(`/tickets/${ticketId}/assign?user_id=${userId}`)
      await fetchTicket(ticketId)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to assign ticket'
      throw err
    }
  }

  async function resolveTicket(ticketId, resolution, resolutionCode = 'fixed') {
    // Store original status for optimistic update
    const ticket = tickets.value.find(t => t.id === ticketId)
    const originalStatus = ticket?.status

    try {
      const response = await api.post(
        `/tickets/${ticketId}/resolve?resolution=${encodeURIComponent(resolution)}&resolution_code=${resolutionCode}`
      )
      await fetchTicket(ticketId)
      // Optimistic stats update
      if (originalStatus && originalStatus !== 'resolved') {
        updateStatsForStatusChange(originalStatus, 'resolved')
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to resolve ticket'
      throw err
    }
  }

  async function closeTicket(ticketId) {
    // Store original status for optimistic update
    const ticket = tickets.value.find(t => t.id === ticketId)
    const originalStatus = ticket?.status

    try {
      const response = await api.post(`/tickets/${ticketId}/close`)
      await fetchTicket(ticketId)
      // Optimistic stats update
      if (originalStatus && originalStatus !== 'closed') {
        updateStatsForStatusChange(originalStatus, 'closed')
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to close ticket'
      throw err
    }
  }

  async function reopenTicket(ticketId, reason = null) {
    // Store original status for optimistic update
    const ticket = tickets.value.find(t => t.id === ticketId)
    const originalStatus = ticket?.status

    try {
      const params = reason ? `?reason=${encodeURIComponent(reason)}` : ''
      const response = await api.post(`/tickets/${ticketId}/reopen${params}`)
      await fetchTicket(ticketId)
      // Optimistic stats update
      if (originalStatus && originalStatus !== 'open') {
        updateStatsForStatusChange(originalStatus, 'open')
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to reopen ticket'
      throw err
    }
  }

  // ==================== Bulk Operations with Optimistic Updates ====================

  async function bulkCloseTickets(ticketIds) {
    const originalStats = { ...stats.value }
    const affectedTickets = tickets.value.filter(t =>
      ticketIds.includes(t.id) && t.status !== 'closed'
    )

    // Optimistic update
    affectedTickets.forEach(ticket => {
      updateStatsForStatusChange(ticket.status, 'closed')
    })

    try {
      const response = await api.post('/tickets/bulk-close', { ticket_ids: ticketIds })
      // Update local ticket statuses
      affectedTickets.forEach(ticket => {
        const idx = tickets.value.findIndex(t => t.id === ticket.id)
        if (idx !== -1) {
          tickets.value[idx] = { ...tickets.value[idx], status: 'closed' }
        }
      })
      return response.data
    } catch (err) {
      // Rollback stats on error
      Object.assign(stats.value, originalStats)
      error.value = err.response?.data?.detail || 'Failed to close tickets'
      throw err
    }
  }

  async function bulkUpdateStatus(ticketIds, newStatus) {
    const originalStats = { ...stats.value }
    const affectedTickets = tickets.value.filter(t =>
      ticketIds.includes(t.id) && t.status !== newStatus
    )

    // Optimistic update
    affectedTickets.forEach(ticket => {
      updateStatsForStatusChange(ticket.status, newStatus)
    })

    try {
      const response = await api.post('/tickets/bulk-status', { ticket_ids: ticketIds, status: newStatus })
      // Update local ticket statuses
      affectedTickets.forEach(ticket => {
        const idx = tickets.value.findIndex(t => t.id === ticket.id)
        if (idx !== -1) {
          tickets.value[idx] = { ...tickets.value[idx], status: newStatus }
        }
      })
      return response.data
    } catch (err) {
      // Rollback stats on error
      Object.assign(stats.value, originalStats)
      error.value = err.response?.data?.detail || 'Failed to update ticket status'
      throw err
    }
  }

  async function bulkAssignTickets(ticketIds, userId) {
    const affectedTickets = tickets.value.filter(t => ticketIds.includes(t.id))
    const originalStates = affectedTickets.map(t => ({ id: t.id, assigned_to_id: t.assigned_to_id, status: t.status }))

    // Optimistic update
    affectedTickets.forEach(ticket => {
      const idx = tickets.value.findIndex(t => t.id === ticket.id)
      if (idx !== -1) {
        tickets.value[idx] = { ...tickets.value[idx], assigned_to_id: userId }
        // Auto-open new tickets when assigned
        if (tickets.value[idx].status === 'new') {
          updateStatsForStatusChange('new', 'open')
          tickets.value[idx].status = 'open'
        }
      }
    })

    try {
      const response = await api.post('/tickets/bulk-assign', { ticket_ids: ticketIds, assigned_to_id: userId })
      return response.data
    } catch (err) {
      // Rollback on error
      originalStates.forEach(original => {
        const idx = tickets.value.findIndex(t => t.id === original.id)
        if (idx !== -1) {
          tickets.value[idx] = { ...tickets.value[idx], assigned_to_id: original.assigned_to_id, status: original.status }
        }
      })
      error.value = err.response?.data?.detail || 'Failed to assign tickets'
      throw err
    }
  }

  async function bulkUpdatePriority(ticketIds, newPriority) {
    const affectedTickets = tickets.value.filter(t => ticketIds.includes(t.id))
    const originalPriorities = affectedTickets.map(t => ({ id: t.id, priority: t.priority }))

    // Optimistic update
    affectedTickets.forEach(ticket => {
      const idx = tickets.value.findIndex(t => t.id === ticket.id)
      if (idx !== -1) {
        // Update by_priority stats
        if (stats.value.by_priority && ticket.priority && stats.value.by_priority[ticket.priority] !== undefined) {
          stats.value.by_priority[ticket.priority] = Math.max(0, stats.value.by_priority[ticket.priority] - 1)
        }
        if (stats.value.by_priority) {
          stats.value.by_priority[newPriority] = (stats.value.by_priority[newPriority] || 0) + 1
        }
        tickets.value[idx] = { ...tickets.value[idx], priority: newPriority }
      }
    })

    try {
      const response = await api.post('/tickets/bulk-priority', { ticket_ids: ticketIds, priority: newPriority })
      return response.data
    } catch (err) {
      // Rollback on error
      originalPriorities.forEach(original => {
        const idx = tickets.value.findIndex(t => t.id === original.id)
        if (idx !== -1) {
          tickets.value[idx] = { ...tickets.value[idx], priority: original.priority }
        }
      })
      await fetchTicketStats() // Refetch stats on error to ensure consistency
      error.value = err.response?.data?.detail || 'Failed to update ticket priority'
      throw err
    }
  }

  async function bulkUpdateType(ticketIds, newType) {
    const affectedTickets = tickets.value.filter(t => ticketIds.includes(t.id))
    const originalTypes = affectedTickets.map(t => ({ id: t.id, ticket_type: t.ticket_type }))

    // Optimistic update
    affectedTickets.forEach(ticket => {
      const idx = tickets.value.findIndex(t => t.id === ticket.id)
      if (idx !== -1) {
        // Update by_type stats
        if (stats.value.by_type && ticket.ticket_type && stats.value.by_type[ticket.ticket_type] !== undefined) {
          stats.value.by_type[ticket.ticket_type] = Math.max(0, stats.value.by_type[ticket.ticket_type] - 1)
        }
        if (stats.value.by_type) {
          stats.value.by_type[newType] = (stats.value.by_type[newType] || 0) + 1
        }
        tickets.value[idx] = { ...tickets.value[idx], ticket_type: newType }
      }
    })

    try {
      const response = await api.post('/tickets/bulk-type', { ticket_ids: ticketIds, ticket_type: newType })
      return response.data
    } catch (err) {
      // Rollback on error
      originalTypes.forEach(original => {
        const idx = tickets.value.findIndex(t => t.id === original.id)
        if (idx !== -1) {
          tickets.value[idx] = { ...tickets.value[idx], ticket_type: original.ticket_type }
        }
      })
      await fetchTicketStats() // Refetch stats on error to ensure consistency
      error.value = err.response?.data?.detail || 'Failed to update ticket type'
      throw err
    }
  }

  function setFilter(key, value) {
    filters.value[key] = value
  }

  function clearFilters() {
    filters.value = {
      status: null,
      priority: null,
      ticket_type: null,
      category: null,
      search: '',
      my_tickets: false
    }
  }

  return {
    // State
    tickets,
    currentTicket,
    stats,
    loading,
    error,
    filters,

    // Getters
    openTickets,
    myTickets,

    // Actions
    fetchTickets,
    fetchTicketStats,
    fetchTicket,
    createTicket,
    updateTicket,
    deleteTicket,
    addComment,
    assignTicket,
    resolveTicket,
    closeTicket,
    reopenTicket,
    bulkCloseTickets,
    bulkUpdateStatus,
    bulkAssignTickets,
    bulkUpdatePriority,
    bulkUpdateType,
    setFilter,
    clearFilters
  }
})
