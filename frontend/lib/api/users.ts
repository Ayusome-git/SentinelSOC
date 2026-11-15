import { api } from '../api'
import { User } from '../types/user'

export const usersApi = {
  getUsers: async (): Promise<{ items: User[], total: number }> => {
    return api.get<{ items: User[], total: number }>('/api/v1/users')
  }
}
