import React, { useState, useRef, useEffect } from 'react';
import { uploadAPI, categoriesAPI } from '../api';
import { useActivity } from '../contexts/ActivityContext';
import '../styles/upload-panel.css';

interface UploadPanelProps {
  userId: string;
  categories: string[];
  onUploadSuccess: (category: string) => void;
  onError: (error: string) => void;
  onDeleteCategory: (category: string) => void;
}

interface CategoryDescription {
  [category: string]: string;
}

interface UploadedFile {
  upload_id: string;
  filename: string;
  category: string;
  size: number;
  created_at: string;
}

export const UploadPanel: React.FC<UploadPanelProps> = ({
  userId,
  categories,
  onUploadSuccess,
  onError,
  onDeleteCategory,
}) => {
  const { addActivity } = useActivity();
  const [descriptions, setDescriptions] = useState<CategoryDescription>({});
  const [editingDescription, setEditingDescription] = useState<string>('');
  const [savingDescription, setSavingDescription] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [newCategory, setNewCategory] = useState<string>('');
  const [isCreatingCategory, setIsCreatingCategory] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset selected category if it no longer exists in categories list
  useEffect(() => {
    if (selectedCategory && !categories.includes(selectedCategory)) {
      console.log('Selected category no longer exists, resetting:', selectedCategory);
      setSelectedCategory('');
      setUploadedFiles([]);
      setEditingDescription('');
    }
  }, [categories, selectedCategory]);

  const handleCategorySelect = async (value: string) => {
    console.log('handleCategorySelect called with:', value);
    if (value === 'new') {
      setIsCreatingCategory(true);
      setSelectedCategory('');
      setNewCategory('');
      setEditingDescription('');
      setUploadedFiles([]);
    } else {
      setSelectedCategory(value);
      setIsCreatingCategory(false);
      setNewCategory('');
      
      // Load category description from API
      try {
        const description = await uploadAPI.getDescription(value);
        setEditingDescription(description || '');
        console.log('✓ Loaded description for category:', value);
      } catch (error) {
        console.error('Error loading description:', error);
        setEditingDescription('');
      }
      
      // Load uploaded files for this category
      try {
        const files = await uploadAPI.listFiles(value);
        setUploadedFiles(files);
        console.log('✓ Loaded files for category:', value, files);
      } catch (error) {
        console.error('Error loading files:', error);
        setUploadedFiles([]);
      }
      
      console.log('selectedCategory set to:', value);
    }
  };

  const handleSaveDescription = async () => {
    if (!selectedCategory || !editingDescription.trim()) {
      onError('Válasszon kategóriát és adjon meg leírást');
      return;
    }

    setSavingDescription(true);
    try {
      await uploadAPI.saveDescription(selectedCategory, editingDescription);
      setDescriptions({
        ...descriptions,
        [selectedCategory]: editingDescription,
      });
      console.log('✓ Description saved for category:', selectedCategory);
    } catch (error: any) {
      onError(error.message || 'Leírás mentés hiba');
    } finally {
      setSavingDescription(false);
    }
  };

  const handleCreateCategory = async () => {
    if (!newCategory.trim()) {
      onError('Kategória neve nem lehet üres');
      return;
    }

    try {
      // Call the API to create the category on backend
      await categoriesAPI.createCategory(newCategory);
      setSelectedCategory(newCategory);
      setNewCategory('');
      setIsCreatingCategory(false);
      // Trigger the upload success handler to refresh the category list
      onUploadSuccess(newCategory);
    } catch (err: any) {
      onError('Kategória létrehozási hiba: ' + (err.message || String(err)));
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Use default category if none selected
    const categoryToUse = selectedCategory || 'Dokumentumok';
    console.log('Uploading to category:', categoryToUse, 'selectedCategory state:', selectedCategory); // Debug

    setUploading(true);
    const activityId = addActivity(`📄 Dokumentum feltöltés: ${file.name}`, 'processing');
    
    try {
      addActivity(`⏳ "${categoryToUse}" kategóriába feltöltés folyamatban...`, 'processing');
      await uploadAPI.uploadFile(categoryToUse, file);
      addActivity(`✓ "${file.name}" sikeresen feldolgozva`, 'success');
      onUploadSuccess(categoryToUse);
      setSelectedCategory('');
      setNewCategory('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      addActivity(`✗ Feltöltési hiba: ${error.message}`, 'error');
      onError(error.message || 'Feltöltési hiba');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-panel">
      <h2>Dokumentum feltöltés</h2>

      <div className="upload-form">
        {/* Category selector */}
        <div className="form-group">
          <label htmlFor="category">Kategória:</label>
          {isCreatingCategory ? (
            <div className="new-category-input">
              <input
                type="text"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                placeholder="Új kategória neve"
              />
              <button onClick={handleCreateCategory}>Létrehozás</button>
              <button
                onClick={() => {
                  setIsCreatingCategory(false);
                  setNewCategory('');
                }}
              >
                Mégse
              </button>
            </div>
          ) : (
            <select 
              value={selectedCategory} 
              onChange={(e) => {
                const value = e.target.value;
                console.log('Selected category:', value); // Debug log
                handleCategorySelect(value);
              }}
            >
              <option value="">-- Válasszon kategóriát --</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
              <option value="new">+ Új kategória</option>
            </select>
          )}
        </div>

        {/* File input */}
        <div className="form-group">
          <label htmlFor="file">Fájl (Markdown):</label>
          <input
            ref={fileInputRef}
            type="file"
            id="file"
            accept=".md"
            onChange={handleFileSelect}
            disabled={uploading}
          />
          {uploading && <span className="loading">Feltöltés...</span>}
          {selectedCategory && !uploading && (
            <small style={{ color: '#666', marginTop: '4px', display: 'block' }}>
              ✓ Kategória: {selectedCategory}
            </small>
          )}
        </div>

        {/* Description input */}
        {selectedCategory && !isCreatingCategory && (
          <div className="form-group">
            <label htmlFor="description">Leírás:</label>
            <textarea
              id="description"
              value={editingDescription}
              onChange={(e) => setEditingDescription(e.target.value)}
              placeholder="pl. a mesterséges inteligenciához kapcsolódó információk"
              rows={3}
              disabled={savingDescription}
            />
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
              <button 
                onClick={handleSaveDescription}
                disabled={savingDescription || !editingDescription.trim()}
              >
                {savingDescription ? 'Mentés...' : '💾 Leírás mentése'}
              </button>
              <button 
                onClick={() => onDeleteCategory(selectedCategory)}
                style={{ backgroundColor: '#d32f2f', color: 'white' }}
                title="Kategória és összes dokumentuma törlése"
              >
                🗑️ Kategória törlése
              </button>
            </div>
            {descriptions[selectedCategory] && (
              <small style={{ color: '#4CAF50', marginTop: '4px', display: 'block' }}>
                ✓ Leírás mentve
              </small>
            )}
          </div>
        )}

        {/* Uploaded files list */}
        {selectedCategory && !isCreatingCategory && uploadedFiles.length > 0 && (
          <div className="form-group">
            <label>📄 Feltöltött dokumentumok:</label>
            <ul style={{ fontSize: '13px', listStyle: 'none', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              {uploadedFiles.map((file) => (
                <li 
                  key={file.upload_id}
                  style={{ 
                    padding: '6px 0',
                    borderBottom: '1px solid #ddd',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span>
                    <strong>{file.filename}</strong><br/>
                    <span style={{ fontSize: '11px', color: '#999' }}>
                      {(file.size / 1024).toFixed(1)} KB - {new Date(file.created_at).toLocaleString('hu-HU')}
                    </span>
                  </span>
                  <button
                    onClick={async () => {
                      try {
                        await uploadAPI.deleteFile(selectedCategory, file.upload_id, file.filename);
                        setUploadedFiles(uploadedFiles.filter(f => f.upload_id !== file.upload_id));
                        console.log('✓ File deleted:', file.filename);
                      } catch (error: any) {
                        onError('Törlési hiba: ' + error.message);
                      }
                    }}
                    style={{ padding: '2px 6px', fontSize: '12px', color: '#d32f2f' }}
                    title="Törlés"
                  >
                    🗑️
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {selectedCategory && !isCreatingCategory && uploadedFiles.length === 0 && (
          <div style={{ padding: '12px', backgroundColor: '#fff3e0', borderRadius: '4px', fontSize: '13px', color: '#f57c00' }}>
            ℹ️ Még nincsenek feltöltött dokumentumok ebben a kategóriában.
          </div>
        )}
      </div>
    </div>
  );
};
