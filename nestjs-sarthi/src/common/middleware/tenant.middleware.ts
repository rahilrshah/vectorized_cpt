import { Injectable, NestMiddleware, BadRequestException, UnauthorizedException, Logger } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { ConfigService } from '@nestjs/config';

export interface TenantRequest extends Request {
  tenant?: {
    id: string;
    name: string;
    permissions: string[];
    isValid: boolean;
  };
}

@Injectable()
export class TenantMiddleware implements NestMiddleware {
  private readonly logger = new Logger(TenantMiddleware.name);
  private readonly tenantHeader: string;
  private readonly validationEnabled: boolean;
  private readonly defaultTenantId: string;

  constructor(private readonly configService: ConfigService) {
    this.tenantHeader = this.configService.get('multiTenant.tenantHeader', 'X-Tenant-Id');
    this.validationEnabled = this.configService.get('multiTenant.tenantValidationEnabled', true);
    this.defaultTenantId = this.configService.get('multiTenant.defaultTenant', 'default');
  }

  async use(req: TenantRequest, res: Response, next: NextFunction) {
    try {
      // Skip tenant validation for health checks and metrics
      if (this.shouldSkipTenantValidation(req.path)) {
        return next();
      }

      // Extract tenant ID from header
      const tenantId = req.headers[this.tenantHeader.toLowerCase()] as string;
      
      if (!tenantId) {
        if (this.validationEnabled) {
          this.logger.warn('Missing tenant ID in request', {
            path: req.path,
            method: req.method,
            ip: req.ip,
            userAgent: req.get('User-Agent'),
          });
          throw new BadRequestException(`Missing required header: ${this.tenantHeader}`);
        } else {
          // Use default tenant for development
          req.tenant = await this.createDefaultTenant();
          return next();
        }
      }

      // Validate and enrich tenant information
      const tenant = await this.validateAndEnrichTenant(tenantId);
      
      if (!tenant.isValid) {
        this.logger.warn('Invalid tenant access attempt', {
          tenantId,
          path: req.path,
          method: req.method,
          ip: req.ip,
        });
        throw new UnauthorizedException('Invalid or unauthorized tenant');
      }

      // Attach tenant context to request
      req.tenant = tenant;

      // Add tenant context to response headers (for debugging in non-prod)
      if (this.configService.get('NODE_ENV') !== 'production') {
        res.setHeader('X-Tenant-Context', JSON.stringify({
          id: tenant.id,
          name: tenant.name,
          permissions: tenant.permissions.length,
        }));
      }

      // Log tenant access (audit trail)
      this.logger.log('Tenant access validated', {
        tenantId: tenant.id,
        tenantName: tenant.name,
        path: req.path,
        method: req.method,
        permissionCount: tenant.permissions.length,
      });

      next();
    } catch (error) {
      this.logger.error('Tenant middleware error', {
        error: error.message,
        path: req.path,
        method: req.method,
        tenantId: req.headers[this.tenantHeader.toLowerCase()],
      });
      next(error);
    }
  }

  private shouldSkipTenantValidation(path: string): boolean {
    const skipPaths = [
      '/health',
      '/ready',
      '/metrics',
      '/api/docs',
      '/favicon.ico',
    ];
    
    return skipPaths.some(skipPath => path.startsWith(skipPath));
  }

  private async createDefaultTenant() {
    return {
      id: this.defaultTenantId,
      name: 'Default Tenant',
      permissions: ['cpt:search', 'cpt:read'],
      isValid: true,
    };
  }

  private async validateAndEnrichTenant(tenantId: string) {
    // TODO: Implement actual tenant validation against database/cache
    // For now, implement basic validation logic
    
    // Validate tenant ID format (UUID or alphanumeric)
    const tenantIdRegex = /^[a-zA-Z0-9-_]+$/;
    if (!tenantIdRegex.test(tenantId)) {
      return {
        id: tenantId,
        name: '',
        permissions: [],
        isValid: false,
      };
    }

    // Temporary allowlist for demo (replace with database lookup)
    const allowedTenants = [
      'sarthi-main',
      'sarthi-clinic-1', 
      'sarthi-clinic-2',
      'demo-tenant',
      'test-tenant',
      this.defaultTenantId,
    ];

    const isValid = allowedTenants.includes(tenantId);
    
    return {
      id: tenantId,
      name: this.getTenantDisplayName(tenantId),
      permissions: this.getTenantPermissions(tenantId),
      isValid,
    };
  }

  private getTenantDisplayName(tenantId: string): string {
    const displayNames = {
      'sarthi-main': 'Sarthi Healthcare - Main',
      'sarthi-clinic-1': 'Sarthi Healthcare - Clinic 1',
      'sarthi-clinic-2': 'Sarthi Healthcare - Clinic 2',
      'demo-tenant': 'Demo Tenant',
      'test-tenant': 'Test Tenant',
      [this.defaultTenantId]: 'Default Tenant',
    };
    
    return displayNames[tenantId] || `Tenant ${tenantId}`;
  }

  private getTenantPermissions(tenantId: string): string[] {
    const basePermissions = ['cpt:search', 'cpt:read'];
    const adminPermissions = [...basePermissions, 'cpt:admin', 'audit:read'];
    
    // Admin tenants get extended permissions
    if (tenantId === 'sarthi-main') {
      return adminPermissions;
    }
    
    return basePermissions;
  }
}