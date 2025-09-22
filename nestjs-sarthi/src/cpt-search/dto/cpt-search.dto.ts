import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsNotEmpty, IsOptional, IsInt, Min, Max, IsBoolean, IsArray, IsNumber } from 'class-validator';
import { Type, Transform } from 'class-transformer';

export class MedicalNoteRequest {
  @ApiProperty({
    description: 'Medical note text to process and extract CPT codes from',
    example: 'Patient underwent arthroscopic knee surgery to repair torn meniscus in right knee',
    minLength: 10,
    maxLength: 10000,
  })
  @IsString()
  @IsNotEmpty()
  @Transform(({ value }) => typeof value === 'string' ? value.trim() : value)
  text: string;

  @ApiPropertyOptional({
    description: 'Maximum number of CPT codes to return',
    example: 20,
    minimum: 1,
    maximum: 100,
    default: 20,
  })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  @Type(() => Number)
  maxResults?: number = 20;

  @ApiPropertyOptional({
    description: 'Minimum similarity threshold for results',
    example: 0.7,
    minimum: 0.1,
    maximum: 1.0,
    default: 0.7,
  })
  @IsOptional()
  @IsNumber()
  @Min(0.1)
  @Max(1.0)
  @Type(() => Number)
  similarityThreshold?: number = 0.7;

  @ApiPropertyOptional({
    description: 'Enable comprehensive multi-code detection',
    example: true,
    default: true,
  })
  @IsOptional()
  @IsBoolean()
  @Type(() => Boolean)
  enableComprehensiveSearch?: boolean = true;
}

export class DirectSearchRequest {
  @ApiProperty({
    description: 'Pre-processed search query for direct CPT code matching',
    example: 'arthroscopic meniscus repair knee',
    minLength: 3,
    maxLength: 500,
  })
  @IsString()
  @IsNotEmpty()
  @Transform(({ value }) => typeof value === 'string' ? value.trim() : value)
  query: string;

  @ApiPropertyOptional({
    description: 'Maximum number of CPT codes to return',
    example: 20,
    minimum: 1,
    maximum: 100,
    default: 20,
  })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  @Type(() => Number)
  maxResults?: number = 20;

  @ApiPropertyOptional({
    description: 'Minimum similarity threshold for results',
    example: 0.7,
    minimum: 0.1,
    maximum: 1.0,
    default: 0.7,
  })
  @IsOptional()
  @IsNumber()
  @Min(0.1)
  @Max(1.0)
  @Type(() => Number)
  similarityThreshold?: number = 0.7;

  @ApiPropertyOptional({
    description: 'CPT code categories to filter by',
    example: ['Surgery', 'Medicine'],
    isArray: true,
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  categories?: string[];
}

export class CptSearchResult {
  @ApiProperty({
    description: 'CPT code',
    example: '29881',
  })
  cptCode: string;

  @ApiProperty({
    description: 'CPT code description',
    example: 'Arthroscopy, knee, surgical; with meniscectomy (medial OR lateral, including any meniscal shaving)',
  })
  description: string;

  @ApiProperty({
    description: 'Procedure category',
    example: 'Surgery',
  })
  category: string;

  @ApiProperty({
    description: 'Code status',
    example: 'active',
  })
  status: string;

  @ApiProperty({
    description: 'Similarity score (0.0 to 1.0)',
    example: 0.92,
  })
  similarity: number;

  @ApiPropertyOptional({
    description: 'Vector distance from query',
    example: 0.08,
  })
  distance?: number;

  @ApiPropertyOptional({
    description: 'Matching terms found in description',
    example: ['arthroscopy', 'knee', 'meniscus'],
    isArray: true,
  })
  matchTerms?: string[];

  @ApiPropertyOptional({
    description: 'Additional metadata',
  })
  metadata?: Record<string, any>;
}

export class ProcessingPipeline {
  @ApiProperty({
    description: 'Extracted text (truncated for display)',
    example: 'Patient underwent arthroscopic knee surgery...',
  })
  extractedText: string;

  @ApiProperty({
    description: 'AI-extracted medical procedures',
    example: 'Arthroscopic surgery for meniscus repair in right knee',
  })
  extractedProcedures: string;

  @ApiProperty({
    description: 'Generated embedding vector dimensions',
    example: 768,
  })
  embeddingDimensions: number;

  @ApiProperty({
    description: 'Primary CPT search results',
    type: [CptSearchResult],
  })
  primaryResults: CptSearchResult[];

  @ApiPropertyOptional({
    description: 'Comprehensive multi-code detection results',
    type: [CptSearchResult],
  })
  comprehensiveResults?: CptSearchResult[];
}

export class MedicalNoteResponse {
  @ApiProperty({
    description: 'Processing pipeline details',
    type: ProcessingPipeline,
  })
  pipeline: ProcessingPipeline;

  @ApiProperty({
    description: 'Final CPT code results',
    type: [CptSearchResult],
  })
  results: CptSearchResult[];

  @ApiProperty({
    description: 'Processing success status',
    example: true,
  })
  success: boolean;

  @ApiProperty({
    description: 'Total processing time in milliseconds',
    example: 1250,
  })
  processingTimeMs: number;

  @ApiProperty({
    description: 'Total number of results found',
    example: 15,
  })
  totalResults: number;

  @ApiProperty({
    description: 'Original query text',
    example: 'Patient underwent arthroscopic knee surgery...',
  })
  originalQuery: string;

  @ApiPropertyOptional({
    description: 'Error message if processing failed',
    example: 'Vector service temporarily unavailable',
  })
  error?: string;

  @ApiPropertyOptional({
    description: 'Processing warnings',
    example: ['Low similarity scores detected'],
    isArray: true,
  })
  warnings?: string[];

  @ApiProperty({
    description: 'Request metadata',
  })
  metadata: {
    tenantId: string;
    requestId: string;
    timestamp: string;
    version: string;
  };
}

export class DirectSearchResponse {
  @ApiProperty({
    description: 'Search results',
    type: [CptSearchResult],
  })
  results: CptSearchResult[];

  @ApiProperty({
    description: 'Search success status',
    example: true,
  })
  success: boolean;

  @ApiProperty({
    description: 'Original search query',
    example: 'arthroscopic meniscus repair',
  })
  query: string;

  @ApiProperty({
    description: 'Search processing time in milliseconds',
    example: 350,
  })
  processingTimeMs: number;

  @ApiProperty({
    description: 'Total number of results found',
    example: 8,
  })
  totalResults: number;

  @ApiPropertyOptional({
    description: 'Error message if search failed',
  })
  error?: string;

  @ApiProperty({
    description: 'Search metadata',
  })
  metadata: {
    tenantId: string;
    requestId: string;
    timestamp: string;
    similarityThreshold: number;
    maxResults: number;
  };
}