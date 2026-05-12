import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface MetricData {
  total_chunks: number;
  total_documents: number;
  avg_query_time: number;
  cache_hit_rate: number;
  embedding_size: number;
  llm_response_time: number;
  retrieval_time: number;
  memory_usage: number;
  cpu_usage: number;
  queries_per_minute: number;
  error_rate: number;
  uptime: number;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  color?: 'primary' | 'success' | 'warning' | 'error';
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  unit, 
  trend, 
  color = 'primary' 
}) => {
  const getColorClasses = () => {
    switch (color) {
      case 'success':
        return 'bg-success-900/20 border-success-500/30 text-success-400';
      case 'warning':
        return 'bg-yellow-900/20 border-yellow-500/30 text-yellow-400';
      case 'error':
        return 'bg-red-900/20 border-red-500/30 text-red-400';
      default:
        return 'bg-primary-900/20 border-primary-500/30 text-primary-400';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return (
          <svg className="w-3 h-3 text-success-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        );
      case 'down':
        return (
          <svg className="w-3 h-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
          </svg>
        );
      default:
        return (
          <svg className="w-3 h-3 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
          </svg>
        );
    }
  };

  return (
    <div className={`p-3 rounded-lg border ${getColorClasses()} shadow-card`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-text-secondary">{title}</span>
        {trend && getTrendIcon()}
      </div>
      <div className="flex items-baseline space-x-1">
        <span className="text-lg font-bold text-text-primary">{value}</span>
        {unit && <span className="text-xs text-text-muted">{unit}</span>}
      </div>
    </div>
  );
};

const Metrics: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        // Get store stats
        const storeStats = await apiService.getStoreStats();
        
        // Get health check for system metrics
        const healthCheck = await apiService.getHealthCheck();
        
        // Mock some additional metrics for now
        const mockMetrics: MetricData = {
          total_chunks: storeStats.data?.total_chunks || 0,
          total_documents: storeStats.data?.total_documents || 0,
          avg_query_time: 2.5,
          cache_hit_rate: 85.2,
          embedding_size: 384,
          llm_response_time: 1.8,
          retrieval_time: 0.3,
          memory_usage: 65.4,
          cpu_usage: 42.1,
          queries_per_minute: 12,
          error_rate: 0.2,
          uptime: 99.8
        };
        
        setMetrics(mockMetrics);
        setError(null);
      } catch (err) {
        setError('Failed to fetch metrics');
        console.error('Metrics fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    // Refresh metrics every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="p-3 rounded-lg bg-card-light border border-card-border animate-pulse">
            <div className="h-4 bg-card rounded w-3/4 mb-2"></div>
            <div className="h-6 bg-card rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-lg bg-red-900/20 border border-red-500/30">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <div className="space-y-4 scrollbar-dark overflow-y-auto max-h-screen">
      {/* System Overview */}
      <div className="p-3 rounded-lg bg-card-light border border-card-border">
        <h3 className="text-sm font-semibold text-text-primary mb-3">System Overview</h3>
        <div className="grid grid-cols-2 gap-2">
          <MetricCard 
            title="Documents" 
            value={metrics.total_documents} 
            color="primary"
            trend="stable"
          />
          <MetricCard 
            title="Chunks" 
            value={metrics.total_chunks} 
            color="primary"
            trend="up"
          />
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="p-3 rounded-lg bg-card-light border border-card-border">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Performance</h3>
        <div className="space-y-2">
          <MetricCard 
            title="Avg Query Time" 
            value={metrics.avg_query_time} 
            unit="s"
            color="success"
            trend="down"
          />
          <MetricCard 
            title="LLM Response" 
            value={metrics.llm_response_time} 
            unit="s"
            color="warning"
            trend="stable"
          />
          <MetricCard 
            title="Retrieval Time" 
            value={metrics.retrieval_time} 
            unit="s"
            color="success"
            trend="down"
          />
        </div>
      </div>

      {/* System Resources */}
      <div className="p-3 rounded-lg bg-card-light border border-card-border">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Resources</h3>
        <div className="space-y-2">
          <MetricCard 
            title="Memory Usage" 
            value={metrics.memory_usage} 
            unit="%"
            color={metrics.memory_usage > 80 ? 'error' : metrics.memory_usage > 60 ? 'warning' : 'success'}
            trend="up"
          />
          <MetricCard 
            title="CPU Usage" 
            value={metrics.cpu_usage} 
            unit="%"
            color={metrics.cpu_usage > 80 ? 'error' : metrics.cpu_usage > 60 ? 'warning' : 'success'}
            trend="stable"
          />
          <MetricCard 
            title="Cache Hit Rate" 
            value={metrics.cache_hit_rate} 
            unit="%"
            color="success"
            trend="up"
          />
        </div>
      </div>

      {/* Activity Metrics */}
      <div className="p-3 rounded-lg bg-card-light border border-card-border">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Activity</h3>
        <div className="space-y-2">
          <MetricCard 
            title="Queries/min" 
            value={metrics.queries_per_minute}
            color="primary"
            trend="stable"
          />
          <MetricCard 
            title="Error Rate" 
            value={metrics.error_rate} 
            unit="%"
            color={metrics.error_rate > 5 ? 'error' : 'success'}
            trend="down"
          />
          <MetricCard 
            title="Uptime" 
            value={metrics.uptime} 
            unit="%"
            color="success"
            trend="stable"
          />
        </div>
      </div>

      {/* Embedding Info */}
      <div className="p-3 rounded-lg bg-card-light border border-card-border">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Embedding Model</h3>
        <div className="space-y-2">
          <MetricCard 
            title="Dimensions" 
            value={metrics.embedding_size}
            color="primary"
            trend="stable"
          />
        </div>
      </div>
    </div>
  );
};

export default Metrics;
