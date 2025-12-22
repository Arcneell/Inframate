<template>
  <div class="flex flex-col h-full">
    <div class="card h-[calc(100vh-140px)] relative overflow-hidden p-0">
        <div id="network-graph" class="w-full h-full bg-slate-50"></div>
        
        <div class="absolute top-4 right-4 bg-white/90 p-4 rounded shadow border border-slate-200 text-xs z-10">
            <h4 class="font-bold mb-2">Legend</h4>
            <div class="flex items-center gap-2 mb-1">
                <span class="w-3 h-3 rounded-full bg-blue-500"></span> Subnet
            </div>
            <div class="flex items-center gap-2 mb-1">
                <span class="w-3 h-3 rounded-full bg-emerald-500"></span> Active IP
            </div>
            <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-slate-400"></span> Other IP
            </div>
        </div>

        <div class="absolute bottom-4 right-4 z-10">
            <Button icon="pi pi-refresh" rounded @click="fetchTopology" :loading="loading" />
        </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { Network } from 'vis-network';
import api from '../api';

const loading = ref(false);
let network = null;

const fetchTopology = async () => {
    loading.value = true;
    try {
        const res = await api.get('/topology');
        const data = res.data;
        
        const container = document.getElementById('network-graph');
        
        const options = {
            nodes: {
                font: {
                    face: 'Inter',
                    size: 14,
                    color: '#334155'
                },
                borderWidth: 2
            },
            edges: {
                color: { color: '#cbd5e1' },
                width: 2,
                smooth: { type: 'continuous' }
            },
            groups: {
                subnet: {
                    color: { background: '#dbeafe', border: '#3b82f6' },
                    shape: 'box',
                    font: { multi: true }
                },
                ip: {
                    shape: 'dot',
                    size: 10
                },
                internet: {
                    color: { background: '#f1f5f9', border: '#64748b' },
                    size: 30
                }
            },
            physics: {
                stabilization: false,
                barnesHut: {
                    springLength: 200,
                    springConstant: 0.04
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200
            }
        };

        if (network) {
            network.destroy();
        }
        
        network = new Network(container, data, options);
        
    } catch (e) {
        console.error("Failed to load topology", e);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    fetchTopology();
});
</script>

<style>
/* Vis Network tooltips */
div.vis-tooltip {
    background-color: #1e293b;
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
    border: none;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
</style>
