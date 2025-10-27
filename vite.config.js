// Importing the defineConfig function and react plugin for vite
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'


// Exporting the vite configuration with defineconfig
export default defineConfig({
  plugins: [react()],
  server: {
    hmr: {
      overlay: false
    }
  }
})