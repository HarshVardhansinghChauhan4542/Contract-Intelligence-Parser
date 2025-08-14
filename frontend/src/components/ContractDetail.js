import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, Download, RefreshCw, CheckCircle, XCircle, 
  Clock, Loader, Users, DollarSign, Calendar, 
  FileText, AlertTriangle, TrendingUp 
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import axios from 'axios';

const ContractDetail = () => {
  const { contractId } = useParams();
  const [contract, setContract] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchContractStatus();
    const interval = setInterval(() => {
      if (status?.status === 'processing' || status?.status === 'pending') {
        fetchContractStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [contractId, status?.status]);

  useEffect(() => {
    if (status?.status === 'completed') {
      fetchContractData();
    }
  }, [status?.status]);

  const fetchContractStatus = async () => {
    try {
      const response = await axios.get(`/contracts/${contractId}/status`);
      setStatus(response.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch contract status');
    } finally {
      setLoading(false);
    }
  };

  const fetchContractData = async () => {
    try {
      const response = await axios.get(`/contracts/${contractId}`);
      setContract(response.data);
    } catch (err) {
      setError('Failed to fetch contract data');
    }
  };

  const downloadContract = async () => {
    try {
      const response = await axios.get(`/contracts/${contractId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', contract.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-500" />;
      case 'processing':
        return <Loader className="w-6 h-6 text-blue-500 loading-spinner" />;
      default:
        return <Clock className="w-6 h-6 text-yellow-500" />;
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatCriticality = (criticality) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800'
    };
    return colors[criticality] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <Loader className="w-8 h-8 text-blue-500 loading-spinner" />
        <span className="ml-2 text-gray-600">Loading contract...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={fetchContractStatus}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const scoreData = contract?.score ? [
    { name: 'Score', value: contract.score, fill: '#10b981' },
    { name: 'Missing', value: 100 - contract.score, fill: '#e5e7eb' }
  ] : [];

  const categoryScores = contract?.extracted_data?.confidence_scores ? 
    Object.entries(contract.extracted_data.confidence_scores).map(([key, value]) => ({
      name: key.charAt(0).toUpperCase() + key.slice(1),
      score: Math.round(value * 100),
      fill: value >= 0.8 ? '#10b981' : value >= 0.6 ? '#f59e0b' : '#ef4444'
    })) : [];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <Link
            to="/contracts"
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Contract Analysis</h1>
            <p className="text-gray-600">ID: {contractId}</p>
          </div>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={fetchContractStatus}
            className="flex items-center space-x-2 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
          {contract && (
            <button
              onClick={downloadContract}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(status?.status)}
            <div>
              <h2 className="text-lg font-semibold">
                Processing Status: {status?.status?.charAt(0).toUpperCase() + status?.status?.slice(1)}
              </h2>
              {status?.status === 'processing' && (
                <p className="text-gray-600">Progress: {status.progress}%</p>
              )}
              {status?.error && (
                <p className="text-red-600">{status.error}</p>
              )}
            </div>
          </div>
          
          {status?.status === 'processing' && (
            <div className="w-48">
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full progress-bar"
                  style={{ width: `${status.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Contract Data */}
      {contract && contract.status === 'completed' && (
        <div className="space-y-6">
          {/* Score Overview */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Overall Score */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                Overall Score
              </h3>
              <div className="flex items-center justify-center">
                <div className="relative w-32 h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={scoreData}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={60}
                        dataKey="value"
                        startAngle={90}
                        endAngle={450}
                      >
                        {scoreData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className={`text-2xl font-bold ${getScoreColor(contract.score)}`}>
                      {contract.score}
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-center text-gray-600 mt-2">
                Contract Completeness Score
              </p>
            </div>

            {/* Category Scores */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Category Breakdown</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={categoryScores}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="score" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

    
          <div className="grid lg:grid-cols-2 gap-6">
            {contract.extracted_data?.parties?.length > 0 && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Contract Parties
                </h3>
                <div className="space-y-3">
                  {contract.extracted_data.parties.map((party, index) => (
                    <div key={index} className="border-l-4 border-blue-500 pl-4">
                      <h4 className="font-semibold">{party.name}</h4>
                      {party.legal_entity && (
                        <p className="text-sm text-gray-600">Entity: {party.legal_entity}</p>
                      )}
                      {party.signatories?.length > 0 && (
                        <p className="text-sm text-gray-600">
                          Signatories: {party.signatories.join(', ')}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {contract.extracted_data?.financial_details && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <DollarSign className="w-5 h-5 mr-2" />
                  Financial Details
                </h3>
                <div className="space-y-3">
                  {contract.extracted_data.financial_details.total_value && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Total Value:</span>
                      <p className="text-lg font-semibold">
                        {contract.extracted_data.financial_details.currency || '$'}
                        {contract.extracted_data.financial_details.total_value.toLocaleString()}
                      </p>
                    </div>
                  )}
                  {contract.extracted_data.financial_details.currency && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Currency:</span>
                      <p>{contract.extracted_data.financial_details.currency}</p>
                    </div>
                  )}
                  {contract.extracted_data.financial_details.line_items?.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Line Items:</span>
                      <ul className="mt-1 space-y-1">
                        {contract.extracted_data.financial_details.line_items.slice(0, 3).map((item, index) => (
                          <li key={index} className="text-sm text-gray-600">
                            {item.description}
                            {item.total && ` - $${item.total}`}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}


            {contract.extracted_data?.payment_structure && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Calendar className="w-5 h-5 mr-2" />
                  Payment Structure
                </h3>
                <div className="space-y-3">
                  {contract.extracted_data.payment_structure.payment_terms && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Payment Terms:</span>
                      <p>{contract.extracted_data.payment_structure.payment_terms}</p>
                    </div>
                  )}
                  {contract.extracted_data.payment_structure.payment_methods?.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Payment Methods:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {contract.extracted_data.payment_structure.payment_methods.map((method, index) => (
                          <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {method}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {contract.extracted_data?.revenue_classification && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Revenue Classification
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-500">Type:</span>
                    {contract.extracted_data.revenue_classification.recurring_payments && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                        Recurring
                      </span>
                    )}
                    {contract.extracted_data.revenue_classification.one_time_payments && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        One-time
                      </span>
                    )}
                  </div>
                  {contract.extracted_data.revenue_classification.billing_cycle && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Billing Cycle:</span>
                      <p>{contract.extracted_data.revenue_classification.billing_cycle}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {contract.gaps?.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2" />
                Gap Analysis
              </h3>
              <div className="space-y-3">
                {contract.gaps.map((gap, index) => (
                  <div key={index} className="border-l-4 border-red-500 pl-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold">{(gap.field || 'Unknown Field').toString().replace('_', ' ').toUpperCase()}</h4>
                      <span className={`px-2 py-1 text-xs rounded ${formatCriticality(gap.criticality)}`}>
                        {gap.criticality || 'unknown'} priority
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{gap.description || 'No description available'}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContractDetail;
