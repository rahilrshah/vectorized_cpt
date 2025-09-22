import { Controller, Get, Header } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { MetricsService } from './metrics.service';
import { Public } from '../common/decorators/public.decorator';

@ApiTags('monitoring')
@Controller()
export class MetricsController {
  constructor(private readonly metricsService: MetricsService) {}

  @Get('metrics')
  @Public()
  @ApiOperation({
    summary: 'Get Prometheus metrics',
    description: 'Returns application metrics in Prometheus format for monitoring and alerting',
  })
  @ApiResponse({
    status: 200,
    description: 'Prometheus metrics in text format',
    content: {
      'text/plain': {
        example: `# HELP cpt_vector_http_requests_total Total number of HTTP requests
# TYPE cpt_vector_http_requests_total counter
cpt_vector_http_requests_total{method="POST",route="/api/v1/cpt-search/medical-note",status_code="200",tenant_id="sarthi-main"} 42

# HELP cpt_vector_search_duration_seconds Duration of CPT searches in seconds
# TYPE cpt_vector_search_duration_seconds histogram
cpt_vector_search_duration_seconds_bucket{tenant_id="sarthi-main",search_type="medical_note",le="0.1"} 15
cpt_vector_search_duration_seconds_bucket{tenant_id="sarthi-main",search_type="medical_note",le="0.25"} 35
cpt_vector_search_duration_seconds_bucket{tenant_id="sarthi-main",search_type="medical_note",le="+Inf"} 42`
      }
    }
  })
  @Header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
  async getMetrics(): Promise<string> {
    return this.metricsService.getMetrics();
  }
}