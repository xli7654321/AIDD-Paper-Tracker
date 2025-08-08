import { Paper } from '@/types/paper';

export const mockPapers: Paper[] = [
  {
    id: '1',
    title: 'Deep Learning Approaches for Molecular Property Prediction in Drug Discovery',
    authors: ['Smith, J.', 'Johnson, A.', 'Williams, M.'],
    abstract: 'Recent advances in deep learning have shown remarkable success in predicting molecular properties crucial for drug discovery. This paper presents a comprehensive study of various neural network architectures including graph neural networks, transformers, and convolutional neural networks for ADMET property prediction. We evaluate these models on several benchmark datasets and demonstrate significant improvements over traditional machine learning approaches.',
    publishedDate: new Date('2024-01-15'),
    source: 'arXiv',
    categories: ['cs.AI', 'physics.chem-ph'],
    relevanceStatus: 'relevant',
    url: 'https://arxiv.org/abs/2401.12345',
  },
  {
    id: '2',
    title: 'AI-Driven Virtual Screening of Natural Product Libraries for Antiviral Drug Discovery',
    authors: ['Chen, L.', 'Kumar, S.', 'Rodriguez, C.', 'Thompson, K.'],
    abstract: 'Virtual screening has become an essential tool in modern drug discovery pipelines. This study leverages artificial intelligence to screen large natural product libraries for potential antiviral compounds. We employed ensemble methods combining molecular docking, machine learning-based activity prediction, and ADMET filtering to identify promising lead compounds.',
    publishedDate: new Date('2024-01-20'),
    source: 'bioRxiv',
    categories: ['bioinformatics'],
    relevanceStatus: 'relevant',
    url: 'https://biorxiv.org/content/10.1101/2024.01.20.123456',
  },
  {
    id: '3',
    title: 'Quantum Chemical Calculations of Drug-Target Interactions Using DFT Methods',
    authors: ['Patel, R.', 'Anderson, E.'],
    abstract: 'Density functional theory (DFT) calculations provide detailed insights into drug-target interactions at the quantum level. This work presents a systematic study of binding energies and electronic properties of various drug molecules with their protein targets. The computational approach offers new perspectives on molecular recognition and binding affinity prediction.',
    publishedDate: new Date('2024-01-18'),
    source: 'ChemRxiv',
    categories: ['theoretical_computational'],
    relevanceStatus: 'untagged',
    url: 'https://chemrxiv.org/engage/chemrxiv/article-details/123456',
  },
  {
    id: '4',
    title: 'Machine Learning Models for Predicting Drug Side Effects from Chemical Structure',
    authors: ['Davis, M.', 'White, S.', 'Brown, T.', 'Miller, J.', 'Wilson, A.'],
    abstract: 'Predicting adverse drug reactions remains a significant challenge in pharmaceutical development. This paper introduces novel machine learning approaches that can predict potential side effects directly from chemical structure information. Our models achieve state-of-the-art performance on standard benchmarks and provide interpretable insights into structure-toxicity relationships.',
    publishedDate: new Date('2024-01-12'),
    source: 'arXiv',
    categories: ['cs.AI'],
    relevanceStatus: 'relevant',
    url: 'https://arxiv.org/abs/2401.11111',
  },
  {
    id: '5',
    title: 'Molecular Dynamics Simulations of Protein-Ligand Binding Kinetics',
    authors: ['Garcia, F.', 'Lee, H.'],
    abstract: 'Understanding the kinetics of protein-ligand binding is crucial for drug design. This study employs extensive molecular dynamics simulations to investigate binding pathways and residence times of various pharmaceutical compounds. The results provide new insights into the relationship between molecular structure and binding kinetics.',
    publishedDate: new Date('2024-01-25'),
    source: 'ChemRxiv',
    categories: ['theoretical_computational'],
    relevanceStatus: 'irrelevant',
    url: 'https://chemrxiv.org/engage/chemrxiv/article-details/789012',
  },
  {
    id: '6',
    title: 'Generative AI for Novel Drug Scaffold Design and Optimization',
    authors: ['Zhang, W.', 'Kim, Y.', 'Martinez, L.'],
    abstract: 'Generative artificial intelligence has emerged as a powerful tool for designing novel molecular scaffolds with desired properties. This research presents a new framework combining variational autoencoders with reinforcement learning to generate drug-like molecules with optimized ADMET properties. The approach demonstrates significant potential for accelerating early-stage drug discovery.',
    publishedDate: new Date('2024-01-30'),
    source: 'bioRxiv',
    categories: ['bioinformatics'],
    relevanceStatus: 'relevant',
    url: 'https://biorxiv.org/content/10.1101/2024.01.30.567890',
  },
];

// Categories based on actual data sources from the backend
export const categoriesBySource = {
  arXiv: [
    { id: 'physics.chem-ph', name: 'Physics - Chemical Physics' },
    { id: 'cs.AI', name: 'Computer Science - Artificial Intelligence' },
    { id: 'cs.LG', name: 'Computer Science - Machine Learning' },
    { id: 'q-bio', name: 'Quantitative Biology' }
  ],
  bioRxiv: [
    { id: 'biochemistry', name: 'Biochemistry' },
    { id: 'bioinformatics', name: 'Bioinformatics' },
    { id: 'biophysics', name: 'Biophysics' },
    { id: 'synthetic biology', name: 'Synthetic Biology' }
  ],
  ChemRxiv: [
    { id: 'theoretical_computational', name: 'Theoretical and Computational Chemistry' },
    { id: 'biological_medicinal', name: 'Biological and Medicinal Chemistry' }
  ]
};

// Flattened categories list for backward compatibility
export const categories = [
  'physics.chem-ph', 'cs.AI', 'cs.LG', 'q-bio',
  'biochemistry', 'bioinformatics', 'biophysics', 'synthetic biology',
  'theoretical_computational', 'biological_medicinal'
];

export const sources = ['arXiv', 'bioRxiv', 'ChemRxiv'];