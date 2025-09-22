import { Module } from '@nestjs/common';
import { VectorEngineService } from './vector-engine.service';

@Module({
  providers: [VectorEngineService],
  exports: [VectorEngineService],
})
export class VectorEngineModule {}