import { Controller, Post, Body, UseGuards, Req, Logger } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { ThrottlerGuard } from '@nestjs/throttler';
import { CptSearchService } from './cpt-search.service';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { TenantRequest } from '../common/middleware/tenant.middleware';
import { 
  MedicalNoteRequest, 
  MedicalNoteResponse, 
  DirectSearchRequest, 
  DirectSearchResponse 
} from './dto/cpt-search.dto';

@ApiTags('cpt-search')
@Controller('cpt-search')
@ApiBearerAuth()
@UseGuards(ThrottlerGuard, JwtAuthGuard)
export class CptSearchController {
  private readonly logger = new Logger(CptSearchController.name);

  constructor(private readonly cptSearchService: CptSearchService) {}

  @Post('medical-note')
  @ApiOperation({
    summary: 'Process medical note and extract CPT codes',
    description: 'Analyzes medical note text using AI to extract relevant CPT codes with similarity scoring',
  })
  @ApiResponse({
    status: 200,
    description: 'Medical note processed successfully',
    type: MedicalNoteResponse,
  })
  @ApiResponse({
    status: 400,
    description: 'Invalid request parameters',
  })
  @ApiResponse({
    status: 401,
    description: 'Authentication required',
  })
  @ApiResponse({
    status: 403,
    description: 'Access denied - tenant not authorized',
  })
  @ApiResponse({
    status: 429,
    description: 'Rate limit exceeded',
  })
  async processMedicalNote(
    @Body() request: MedicalNoteRequest,
    @Req() req: TenantRequest,
  ): Promise<MedicalNoteResponse> {
    const startTime = Date.now();
    const requestId = req.requestId || 'unknown';
    const tenantId = req.tenant?.id || 'unknown';

    this.logger.log('Processing medical note', {
      requestId,
      tenantId,
      textLength: request.text.length,
      maxResults: request.maxResults,
    });

    try {
      const result = await this.cptSearchService.processMedicalNote(
        request.text,
        {
          tenantId,
          maxResults: request.maxResults,
          similarityThreshold: request.similarityThreshold,
          enableComprehensiveSearch: request.enableComprehensiveSearch,
        },
      );

      const processingTime = Date.now() - startTime;

      const response: MedicalNoteResponse = {
        pipeline: {
          extractedText: result.extractedText,
          extractedProcedures: result.extractedProcedures,
          embeddingDimensions: result.embeddingDimensions,
          primaryResults: result.primaryResults,
          comprehensiveResults: result.comprehensiveResults,
        },
        results: result.results,
        success: true,
        processingTimeMs: processingTime,
        totalResults: result.results.length,
        originalQuery: request.text,
        metadata: {
          tenantId,
          requestId,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      };

      this.logger.log('Medical note processing completed', {
        requestId,
        tenantId,
        processingTime,
        resultCount: result.results.length,
      });

      return response;
    } catch (error) {
      this.logger.error('Medical note processing failed', {
        requestId,
        tenantId,
        error: error.message,
        textLength: request.text.length,
      });

      return {
        pipeline: {
          extractedText: request.text.substring(0, 100) + '...',
          extractedProcedures: '',
          embeddingDimensions: 0,
          primaryResults: [],
        },
        results: [],
        success: false,
        processingTimeMs: Date.now() - startTime,
        totalResults: 0,
        originalQuery: request.text,
        error: error.message,
        metadata: {
          tenantId,
          requestId,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      };
    }
  }

  @Post('direct')
  @ApiOperation({
    summary: 'Direct CPT code search',
    description: 'Performs direct vector search for CPT codes without AI preprocessing',
  })
  @ApiResponse({
    status: 200,
    description: 'Search completed successfully',
    type: DirectSearchResponse,
  })
  async directSearch(
    @Body() request: DirectSearchRequest,
    @Req() req: TenantRequest,
  ): Promise<DirectSearchResponse> {
    const startTime = Date.now();
    const requestId = req.requestId || 'unknown';
    const tenantId = req.tenant?.id || 'unknown';

    this.logger.log('Performing direct CPT search', {
      requestId,
      tenantId,
      query: request.query,
      maxResults: request.maxResults,
    });

    try {
      const results = await this.cptSearchService.directSearch(
        request.query,
        {
          tenantId,
          maxResults: request.maxResults,
          similarityThreshold: request.similarityThreshold,
          categories: request.categories,
        },
      );

      const processingTime = Date.now() - startTime;

      const response: DirectSearchResponse = {
        results,
        success: true,
        query: request.query,
        processingTimeMs: processingTime,
        totalResults: results.length,
        metadata: {
          tenantId,
          requestId,
          timestamp: new Date().toISOString(),
          similarityThreshold: request.similarityThreshold || 0.7,
          maxResults: request.maxResults || 20,
        },
      };

      this.logger.log('Direct search completed', {
        requestId,
        tenantId,
        processingTime,
        resultCount: results.length,
      });

      return response;
    } catch (error) {
      this.logger.error('Direct search failed', {
        requestId,
        tenantId,
        error: error.message,
        query: request.query,
      });

      return {
        results: [],
        success: false,
        query: request.query,
        processingTimeMs: Date.now() - startTime,
        totalResults: 0,
        error: error.message,
        metadata: {
          tenantId,
          requestId,
          timestamp: new Date().toISOString(),
          similarityThreshold: request.similarityThreshold || 0.7,
          maxResults: request.maxResults || 20,
        },
      };
    }
  }
}