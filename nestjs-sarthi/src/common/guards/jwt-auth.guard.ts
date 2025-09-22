import { Injectable, ExecutionContext, UnauthorizedException, Logger, Inject } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ConfigService } from '@nestjs/config';
import { Reflector } from '@nestjs/core';
import { IS_PUBLIC_KEY } from '../decorators/public.decorator';
import { GatewayService } from '../../gateway/gateway.service';

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  private readonly logger = new Logger(JwtAuthGuard.name);

  constructor(
    private reflector: Reflector,
    private configService: ConfigService,
    @Inject(GatewayService) private gatewayService: GatewayService,
  ) {
    super();
  }

  async canActivate(context: ExecutionContext): Promise<boolean> {
    // Check if route is marked as public
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);

    if (isPublic) {
      return true;
    }

    // Check if authentication is disabled in development
    const isDevelopment = this.configService.get('NODE_ENV') === 'development';
    const authDisabled = this.configService.get('AUTH_DISABLED') === 'true';
    
    if (isDevelopment && authDisabled) {
      this.logger.warn('Authentication bypassed in development mode');
      return true;
    }

    // Enhanced Sarthi OAuth 2.0 validation
    const request = context.switchToHttp().getRequest();
    const token = this.extractTokenFromHeader(request);
    
    if (token) {
      try {
        // Validate token with Sarthi auth service
        const authResult = await this.gatewayService.validateToken(token);
        
        if (authResult && authResult.valid) {
          // Attach Sarthi user context to request
          request.user = {
            ...authResult.user,
            sarthiContext: {
              tenantId: authResult.tenantId,
              roles: authResult.roles,
              permissions: authResult.permissions,
              sessionId: authResult.sessionId,
              deviceId: authResult.deviceId,
              lastActivity: new Date(),
            },
          };
          
          this.logger.log('Sarthi OAuth 2.0 authentication successful', {
            userId: authResult.user.id,
            tenantId: authResult.tenantId,
            roles: authResult.roles,
            path: request.url,
          });
          
          return true;
        }
      } catch (error) {
        this.logger.error('Sarthi OAuth 2.0 validation failed', {
          error: error.message,
          path: request.url,
          method: request.method,
        });
      }
    }

    // Fallback to standard JWT validation
    return super.canActivate(context) as Promise<boolean>;
  }

  handleRequest(err: any, user: any, info: any, context: ExecutionContext) {
    const request = context.switchToHttp().getRequest();
    
    if (err || !user) {
      this.logger.warn('JWT authentication failed', {
        error: err?.message,
        info: info?.message,
        path: request.url,
        method: request.method,
        ip: request.ip,
        userAgent: request.get('User-Agent'),
      });
      
      throw err || new UnauthorizedException('Invalid or expired token');
    }

    // Log successful authentication
    this.logger.log('JWT authentication successful', {
      userId: user.sub,
      username: user.username,
      tenantId: user.tenantId,
      path: request.url,
      method: request.method,
    });

    return user;
  }

  private extractTokenFromHeader(request: any): string | null {
    const authHeader = request.headers.authorization;
    if (!authHeader) {
      return null;
    }

    const [type, token] = authHeader.split(' ');
    return type === 'Bearer' ? token : null;
  }
}