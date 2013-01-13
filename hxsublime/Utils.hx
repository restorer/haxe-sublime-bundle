package hxsublime;



import haxe.macro.Context;
import haxe.macro.Expr;


import haxe.macro.TypeTools;

import haxe.macro.Type;


using haxe.macro.ExprTools;

class Utils 
{


	@:macro public static function getEnumConstructors (expr:Expr, pretty:Bool):Expr {

		var t = Context.typeof(expr);
		var res = [];
		switch (t) {
			case Type.TEnum(t, p):
				var constructs = t.get().constructs;

				for (c in constructs) {
					var params = [];
					switch (c.type) {
						case TFun(args, ret):
							for (a in args) {
								params.push(a.name);
							}
						case _:
					}
					res.push({ name: c.name, params:params });
				}
			case _:
		}
		
	 	function constructorString (p:{name:String, params:Array<String>}) {
	 		var str = "";
	 		str += "\tcase " + p.name;
			if (p.params.length > 0) {
				str += "(";
				var first = true;
				for (x in p.params) {
					if (first) {
						first = false;
					} else {
						str += ", ";
					}
					str += x;
				}
				str += ")";
			}
			return str;
	 	}

		res.reverse();
		var str = "<switchExpr>\nswitch (" + expr.toString() + ") {\n";
		var max = 0;
		for (p in res) {
			max = Std.int(Math.max(constructorString(p).length, max));
		}


		for (p in res) {

			var s = constructorString(p);
			str += s;
			for (i in s.length...max) {
				str += " ";
			}

			str += ": \n";
		}
		
		str += "}\n</switchExpr>";

		return Context.makeExpr(str, Context.currentPos());
	}

	@:macro public static function findOccurences (e:Expr):Expr {
		
		
		var type = Context.typeof(e);

		

		Context.onGenerate(function (types) {
			
			for(t in types) {

				switch (t) {
					case Type.TInst(t, params) if (t.get().name == "HeyHo"):
						
						var statics = t.get().statics.get();
						if (statics.length > 0) {
							var static0 = statics[0];
							var typedExpr = static0.expr();
							//trace(typedExpr);

						}
					case _:
						
				}
				
			}
		});

		return macro null;
	}

	@:macro public static function getTypeOfExpr (e:Expr):Expr {
		
		return Context.makeExpr("<type>" + haxe.macro.TypeTools.toString(haxe.macro.Context.typeof(e)) + "</type>", Context.currentPos());

	}

	@:macro public static function checkEField (e:Expr, method:String):Expr 
	{
		var infos = Context.getPosInfos(e.pos);
		var str = "@" + infos.file + "|"+(infos.max + 1)+"-"+(infos.max + 1 + method.length);
		trace(str);
		//trace(originalExpr.toString());
		trace(Context.typeof(e));

		return e;
	}

	#if !macro @:macro #end 
	public static function find (module:String, className:String, method:String, expr:Expr):Expr {

		function f (ex:Expr):Expr {
			return find(module, className, method, ex);
		}
		if (expr == null) return null;

		switch (expr.expr) {
			case EConst( c  ): 
			case EArray( e1 , e2  ): expr.expr = EArray(f(e1), f(e2)); 
			case EBinop( op , e1 , e2  ): expr.expr = EBinop(op, f(e1), f(e2));
			case EField( e , field  ): 

				var methodStr = Context.makeExpr(method, Context.currentPos());
				if (field == method) expr.expr = EField((macro hxsublime.Utils.checkEField(${f(e)}, $methodStr)), field)
				else expr.expr = EField(f(e), field);
				
			case EParenthesis( e  ): expr.expr = EParenthesis(f(e));

			case EObjectDecl( fields):
				for (field in fields) {
					field.expr = f(field.expr);
				}
			case EArrayDecl( values):
				var v = [];
				for (v1 in values) {
					v.push(f(v1));
				}
				expr.expr = EArrayDecl(v);

			case ECall( e , params):
				expr.expr = ECall(f(e), params);				
			case ENew( t , params ):
				for (p in params) {
					p.expr = f(p).expr;
				}

			case EUnop( op , postFix , e ):
				expr.expr = EUnop( op , postFix , f(e) );
			case EVars( vars ):
				
				for (v in vars) {
					v.expr = f(v.expr);
				}
				expr.expr = EVars(vars);
			case EFunction( name , fn  ):
				fn.expr = f(fn.expr);
			case EBlock( exprs  ):
				var v = [];
				for (v1 in exprs) {
					v.push(f(v1));
				}
				expr.expr = EBlock(v);				
			case EFor( it , expr ):
				expr.expr = EFor(f(it), f(expr));
			case EIn( e1, e2 ):
				expr.expr = EIn(f(e1), f(e2));
			case EIf( econd, eif, eelse  ):
				expr.expr = EIf(f(econd), f(eif), f(eelse));
			case EWhile( econd, e, normalWhile  ):
				expr.expr = EWhile(f(econd), f(e), normalWhile);
			case ESwitch( e, cases , edef  ):
				for (c in cases) {
					c.guard = f(c.guard);
					c.expr = f(c.expr);
				}
				expr.expr = ESwitch(f(e), cases, f(edef));
			case ETry( e, catches  ):
				for (c in catches) {
					c.expr = f(c.expr);
				}
				expr.expr = ETry(f(e), catches);
			case EReturn( e  ):
				expr.expr = EReturn(f(e));
			case EBreak:
			case EContinue:
			case EUntyped( e ):
				expr.expr = EUntyped(f(e));
			case EThrow( e ):
				expr.expr = EThrow(f(e));
			case ECast( e, t  ):
				expr.expr = ECast(f(e), t);
			case EDisplay( e, isCall  ):
			case EDisplayNew( t  ):
			case ETernary( econd, eif, eelse ):
				expr.expr = ETernary(f(econd), f(eif), f(eelse));
			case ECheckType( e, t  ): 
				expr.expr = ECheckType(f(e), t);
			case EMeta( s , e ):

				for (p in s.params) {
					p.expr = f(p).expr;
				}
				expr.expr = EMeta(s, f(e));
			#if !haxe3
			case EType( e, field  ):
				expr.expr = EType(f(e), field);
			#end
		}



		return expr;

	}

	@:macro public static function register ():Array<haxe.macro.Expr.Field>
	{
		var fields = Context.getBuildFields();
		
		for (f in fields) {
			switch (f.kind) {
				case FieldType.FFun(f):
					f.expr = macro hxsublime.Utils.find("hxsublime.UtilsTest", "Jup", "juppi", ${f.expr});
				case _:
			}
		}


		return fields;
	}


}