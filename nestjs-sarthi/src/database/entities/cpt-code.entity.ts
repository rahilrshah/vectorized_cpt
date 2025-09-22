import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

@Entity('cpt_codes')
@Index(['tenantId', 'cptCode'], { unique: true })
@Index(['tenantId', 'category'])
@Index(['tenantId', 'status'])
export class CptCode {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'tenant_id', length: 100 })
  @Index()
  tenantId: string;

  @Column({ name: 'cpt_code', length: 10 })
  @Index()
  cptCode: string;

  @Column({ name: 'description', type: 'text' })
  description: string;

  @Column({ name: 'category', length: 100, nullable: true })
  category: string;

  @Column({ name: 'status', length: 20, default: 'active' })
  status: string;

  @Column({ name: 'vector_embedding', type: 'jsonb', nullable: true })
  vectorEmbedding: number[];

  @Column({ name: 'encrypted_data', type: 'text', nullable: true })
  encryptedData: string;

  @Column({ name: 'data_classification', length: 20, default: 'public' })
  dataClassification: string; // public, restricted, confidential, phi

  @Column({ name: 'created_by', length: 100, nullable: true })
  createdBy: string;

  @Column({ name: 'updated_by', length: 100, nullable: true })
  updatedBy: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @Column({ name: 'version', type: 'integer', default: 1 })
  version: number;

  @Column({ name: 'metadata', type: 'jsonb', nullable: true })
  metadata: Record<string, any>;

  // Virtual fields for search results
  similarity?: number;
  distance?: number;
  matchTerms?: string[];
}