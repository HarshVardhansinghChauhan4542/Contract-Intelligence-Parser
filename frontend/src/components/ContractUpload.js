import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { Upload, File, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import axios from 'axios';

const ContractUpload = () => {
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, success, error
  const [uploadedFile, setUploadedFile] = useState(null);
  const [contractId, setContractId] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    
    if (!file) return;
    
    if (file.type !== 'application/pdf') {
      setError('Only PDF files are supported');
      setUploadStatus('error');
      return;
    }
    
    if (file.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB');
      setUploadStatus('error');
      return;
    }

    setUploadedFile(file);
    setUploadStatus('uploading');
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/contracts/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setContractId(response.data.contract_id);
      setUploadStatus('success');
      
      setTimeout(() => {
        navigate(`/contracts/${response.data.contract_id}`);
      }, 2000);

    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setUploadStatus('error');
    }
  }, [navigate]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false,
    maxSize: 50 * 1024 * 1024 
  });

  const resetUpload = () => {
    setUploadStatus('idle');
    setUploadedFile(null);
    setContractId(null);
    setError('');
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Upload Contract for Analysis
        </h1>
        <p className="text-lg text-gray-600">
          Upload a PDF contract to extract key information and analyze its completeness
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-8">
        {uploadStatus === 'idle' && (
          <div
            {...getRootProps()}
            className={`file-drop-zone border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${
              isDragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              {isDragActive ? 'Drop the file here' : 'Drag & drop a PDF contract'}
            </h3>
            <p className="text-gray-500 mb-4">or click to select a file</p>
            <div className="text-sm text-gray-400">
              <p>Supported format: PDF</p>
              <p>Maximum file size: 50MB</p>
            </div>
          </div>
        )}

        {uploadStatus === 'uploading' && uploadedFile && (
          <div className="text-center py-12">
            <Loader className="w-16 h-16 text-blue-500 mx-auto mb-4 loading-spinner" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Uploading Contract
            </h3>
            <p className="text-gray-500 mb-4">
              File: {uploadedFile.name}
            </p>
            <p className="text-sm text-gray-400">
              Processing will begin automatically after upload
            </p>
          </div>
        )}

        {uploadStatus === 'success' && uploadedFile && contractId && (
          <div className="text-center py-12 fade-in">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Upload Successful!
            </h3>
            <p className="text-gray-500 mb-4">
              File: {uploadedFile.name}
            </p>
            <p className="text-sm text-gray-400 mb-6">
              Contract ID: {contractId}
            </p>
            <p className="text-sm text-blue-600">
              Redirecting to contract analysis...
            </p>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="text-center py-12 fade-in">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Upload Failed
            </h3>
            <p className="text-red-600 mb-6">{error}</p>
            <button
              onClick={resetUpload}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}
      </div>

      <div className="mt-12 grid md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <File className="w-12 h-12 text-blue-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Automatic Extraction</h3>
          <p className="text-gray-600">
            Extract parties, financial details, payment terms, and SLA information
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Quality Scoring</h3>
          <p className="text-gray-600">
            Get completeness scores and identify missing critical information
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Gap Analysis</h3>
          <p className="text-gray-600">
            Identify missing fields and receive actionable recommendations
          </p>
        </div>
      </div>
    </div>
  );
};

export default ContractUpload;
