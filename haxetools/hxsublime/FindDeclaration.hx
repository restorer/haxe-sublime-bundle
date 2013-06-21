package hxsublime;


#if macro
using haxe.macro.ExprTools;
using haxe.macro.TypeTools;

import haxe.ds.Option;
import haxe.macro.Context;
import haxe.macro.Expr;
import haxe.macro.Expr.ExprOf;
import haxe.macro.Type;
import haxe.macro.TypeTools;
import neko.Lib;
using StringTools;

typedef FieldInfosData = ResultKindCast;

abstract ResultKindCast (ResultKind) {
	function new (rk:ResultKind) this = rk;

	@:from public static function fromEnumType(t:EnumType) {
		return new ResultKindCast(RKEnumType(t));
	}
	@:from public static function fromDefType(t:DefType) {
		return new ResultKindCast(RKDefType(t));
	}
	@:from public static function fromClassType(t:ClassType) {
		return new ResultKindCast(RKClassType(t));
	}

	@:from public static function fromAnonType(t:AnonType) {
		return new ResultKindCast(RKAnonType(t));
	}

	@:from public static function fromAbstractType(t:AbstractType) {
		return new ResultKindCast(RKAbstractType(t));
	}
	@:from public static function fromClassField(t:ClassField) {
		if (t == null) throw "t is null";
		
		return new ResultKindCast(RKClassField(t));
	}

	public var pos(get, never):Position;
	public var name(get, never):String;
	public var doc(get, never):Null<String>;
	
	function get_name() {
		return switch (this) {
			
			case RKEnumType(f): f.name;
			case RKDefType(f): f.name;
			case RKAnonType(f): "anon";
			case RKClassType(f): f.name;
			case RKAbstractType(f): f.name;
			case RKClassField(f): f.name;
		}
	}
	function get_doc() {
		return switch (this) {
			
			case RKEnumType(f): f.doc;
			case RKDefType(f): f.doc;
			case RKAnonType(f): f.fields[0].doc;
			case RKClassType(f): f.doc;
			case RKAbstractType(f): f.doc;
			case RKClassField(f): f.doc;
		}
	}
	function get_pos() {
		return switch (this) {
			case RKEnumType(f): f.pos;
			case RKDefType(f): f.pos;
			case RKAnonType(f): f.fields[0].pos;
			case RKClassType(f): f.pos;
			case RKAbstractType(f): f.pos;
			case RKClassField(f): f.pos;
		}
	}

	static function typestr (type:Type) {
		return TypeTools.toString(type).split("#").join("");
	}

	static function isStaticClass (type:Type) {
		return TypeTools.toString(type).indexOf("#") > -1;	
	}

	public function info(type:Type) {

		function infoTFun(cf:ClassField, args, ret ) {
			trace(cf.type);
			function paramToString (t) return t.name + ":" + TypeTools.toString(t.t);
			var signature = "(" + args.map(paramToString).join(", ") + "): " + TypeTools.toString(ret);

			var infix = if (isStaticClass(type)) "::" else ".";
			return typestr(type) + infix + cf.name + signature;
		}

		return switch (this) {
			case RKEnumType(f): "enum " + typestr(type);
			case RKDefType(f): 
				function ts (t:Type):String {
					return switch (t) {
						case TInst(_,_): "class " + typestr(type);
						case TEnum(_,_): "enum " + typestr(type);
						case TType(tt,_): 
							trace(tt);
							ts(tt.get().type);

						case TAnonymous(a): 

							if (isStaticClass(type)) {
								
								var ct = TypeTools.toComplexType(t);
								var typeStr = typestr(type);
								var newType = Context.typeof(Context.parse('{ var x : $typeStr = null; x; }', Context.currentPos()));
								ts(newType);
							} else {
								trace(TypeTools.toString(type));
								trace("its anon");
								"typedef " + typestr(type);
							}
						case TAbstract(_,_): "abstract " + typestr(type);
						case TFun(_,_): "function " + typestr(type);
						case TMono(_): "TMono";
						case TLazy(t1): ts(t1());
						case _ : "other";
					}
				}
				ts(f.type);
			case RKAnonType(f): "typedef " + typestr(type);
			case RKClassType(f): "class " + typestr(type);
			case RKAbstractType(f): "abstract" + typestr(type);
			case RKClassField(cf = { kind : FVar(vk,va)}): 
				var infix = if (isStaticClass(type)) "::" else ".";
				typestr(type) + infix + cf.name;
			case RKClassField(cf = { type : TFun(args,ret)}): 
				infoTFun(cf, args, ret);
			case RKClassField(cf = { type : TLazy(lazyT)}):
				switch (lazyT()) {
					case TFun(args, ret):
						infoTFun(cf, args, ret);
					case _ : 
						"lazy other";
				}
			case RKClassField(cf):
				trace(cf); 
				"other";

		}
	}
}


enum ResultKind {
	RKEnumType(t:EnumType);
	RKClassType(t:ClassType);
	RKDefType(t:DefType);
	RKAnonType(t:AnonType);
	RKAbstractType(t:AbstractType);
	RKClassField(f:ClassField);
}

typedef FieldInfosWithTypeData = {
	field:FieldInfosData,
	type:Type,
	isStatic:Bool
}

typedef FieldInfos = Option<FieldInfosWithTypeData>; 
#end



class FindDeclaration 
{


	#if macro

	static function mkFieldInfos(field:FieldInfosData, t:Type, isStatic:Bool = false) {
		return Some({ field: field, type:t, isStatic:isStatic});
	}

	static function outResult (info:FieldInfos, success:FieldInfosWithTypeData->String = null, error = null) {
		if (error == null) {
			error = function () return "";
		}
		if (success == null) {
			success = function (f) return formatPos(f.field.pos);
		}


		switch (info) {
			case Some(f): 
				
				out(success(f));
			case None: out(error());
		}

	}

	static function formatPos (pos:Position) 
	{
		var p = Context.getPosInfos( pos );
		var file = p.file.split("\\").join("/");
		return '|||||{ "file": "$file", "min" : ${p.min}, "max" : ${p.max} }|||||';
	}

	static function formatDoc (d:FieldInfosWithTypeData) 
	{

		var isStatic = d.isStatic || switch (d.type) {
			case TType(dt,_):
				StringTools.startsWith(dt.get().name,"#");
			case _: false;

		}

		var info = d.field.info(d.type);
		var infix = isStatic ? "::" : ".";

		trace("info:" + info);
		
		var typestr = info;

		var doc = d.field.doc;
		var doc = doc == null ? "" : doc;
		function removeStar (s) {
			return StringTools.ltrim(if (StringTools.startsWith(s,"*")) s.substr(1) else s);
		}
		doc = doc.split("\n").map(StringTools.ltrim).map(removeStar).join("\n");
		doc = doc.split("\n").join("\\n").split("\t").join("\\t").split('"').join('\\"').split("\r").join("");

		doc = typestr + "\\n" + doc;
		return '|||||{ "doc": "$doc" }|||||';
	}

	static function redirectTrace () 
	{
		
		haxe.Log.trace = function (msg, ?pos:haxe.PosInfos) 
		{
			var f = pos.fileName;
			var p = f.substr(f.lastIndexOf("/")+1) + ":" + pos.lineNumber;
			out(p + ": " + msg);
		}
	}

	static function error (info:String = "impossible") 
	{
		return '|||||{ "error": "${info}" }|||||';
	}

	static function fromIdent (x):FieldInfos 
	{
		trace("FROM IDENT");
		var currentType = Context.getLocalType();
		var r = if (currentType != null) {
			searchField(currentType, check.bind(_, ExprTools.toString(x)));
		} else {
			None;
		}
		return if (r == None) {
			try {
				var t = Context.typeof( x );

				var info:FieldInfos = switch (t) {
					case Type.TAbstract( t1 , _ ): mkFieldInfos(t1.get(), t);
					case Type.TEnum( t1 , _ ):     mkFieldInfos(t1.get(), t);
					case Type.TInst( t1 , _ ):     mkFieldInfos(t1.get(), t);
					case Type.TType( t1 , _ ):     mkFieldInfos(t1.get(), t);
					case Type.TAnonymous( t1 ):    mkFieldInfos(t1.get(), t);
					//case Type.TFun( _,_ ):  
						
					case _: None;
				}
				info;

			} catch (e:Dynamic) {
				None;
			}
		} else r;
	}

	static function findInInstance (t:Ref<ClassType>, ttype:Type, check):FieldInfos
	{
		var cur = t;

		var res:FieldInfos = None;
		var interf1 = [];

		var statics = t.get().statics.get().filter( check );
		if (statics.length > 0) {
			return mkFieldInfos(statics[0], ttype, true);
		}
		
		
		while (res == None) {

			var fields = cur.get().fields.get().filter( check );
			
			if (fields.length == 1)  {
				var x:FieldInfosData = fields[0];

				res = mkFieldInfos(x, ttype);
			} 
			else 
			{
				var x = cur.get().superClass;
				if (x == null) break;

				cur = x.t;
				ttype = TInst(cur,x.params);

				for (i in cur.get().interfaces) {

					interf1.push(i);
				}
			}
		}
		if (res == None) {
			var interf = t.get().interfaces.concat(interf1);
			while (res == None && interf.length > 0) {
				var new_interf = [];
				for (i in interf) {
					var fields = i.t.get().fields.get().filter( check );
					if (fields.length == 1)  {
						res = mkFieldInfos(fields[0], TInst(i.t, i.params));
						
					} else {
						for (i in i.t.get().interfaces) {
							new_interf.push(i);
						}
					}
				}
				if (res == None) {
					interf = new_interf;	
				}
				
			}
		}

		return res;
	}

	static function check (x:ClassField, field:String) 
	{
		return if (field.startsWith("get_") || field.startsWith("set_")) 
		{
			x.name == field.substr(4);
		} else {
			x.name == field;
		}
	}

	static function searchField(t, check) {
		return switch (t) 
		{
			case Type.TInst( t1 , _ ):
				trace("Search in TInst");
				findInInstance(t1, t, check);

				
			case Type.TType( t1 , _ ):
				trace("Search in TType");
				switch (t1.get().type) {
					case Type.TInst( t2 , _ ):
						trace("Search in TInst");
						var statics = t2.get().statics.get().filter( check );
						//var fields = t.get().fields.get().filter( check );

						//trace(t.get());
						if (statics.length == 0) {
							var fields = t2.get().fields.get().filter( check );
							if (fields.length == 0) 
								None 
							else
								mkFieldInfos(fields[0], t, true);
						} else {
							mkFieldInfos(statics[0], t, true);
						}
						
						

					case Type.TAnonymous( a ):
						trace("TAnonymous");
						var fields = a.get().fields.filter(check);
						if (fields.length > 0) {
							mkFieldInfos(fields[0], t);
						} else {
							try {
								var t = Context.getType(TypeTools.toString(t).split("#").join(""));
								searchField(t, check);
							}
							catch(e:Dynamic) 
							{
								None;
							}
							
						}

					case _: 
						trace("unsupported");
						None;


				}
			case Type.TAnonymous( a ):
				trace("Search in TAnonymous");
				var fields = a.get().fields.filter(check);

				if (fields.length > 0) {
					mkFieldInfos(fields[0], t);
				} else {
					None;
				}

			case Type.TAbstract( a,_ ):
				trace("Search in TAbstract");
				

				var fields = a.get().impl.get().statics.get().filter(check);

				if (fields.length > 0) {
					mkFieldInfos(fields[0], t);
				} else {
					None;
				}

			case _:

				trace("Declaration is not available");
				None;
		}
	}

	static function fromField (x, field:String):FieldInfos
	{
		out(field);
		var check = check.bind(_, field);

		var info:FieldInfos = try {
			trace("Trying to get the type of expression x");
			trace("this could fail/stop without a thrown exception (Haxe Compiler Bug in Display mode)");
			var t = Context.typeof( x );
			trace("x was successfull typed as: << " + TypeTools.toString(t) + " >>");
			
			searchField(t, check);

			// jump to field
			// consider using
			
		}  catch (e:Dynamic) {
			
			// jump to type
			trace("no type");

			var x2 = macro $x.$field;

			fromIdent(x2);

			
		}
		
		return info;

	}

	static var out = Lib.println;

	static function checkRegular (e):FieldInfos 
	{
		
		return switch (e.expr) 
		{
			case EConst(CIdent(_)):
				trace("Current Expression is an const Ident");
				var p = fromIdent(e);
				p;
			case EField(e, field):
				trace("Current Expression is a field access (EField)");
				var p = fromField(e,field);

				if (p == null) 
					out(error());
				p;
				

			// compiler inlined expression
			case ECall({expr:EFunction(_,
				{ expr : { expr : 
					EReturn( 
						{ expr : EFunction(_, { expr : { expr : EReturn(
							x
						)}})}
					)
				}})}, _):
				trace("Current Expression is a compiler inlined Expression (hard to follow)");
				switch (x) 
				{
					case {expr:ECall({ expr : EField(e, field)}, _)}:
						trace("Inlined Expression contains Field Access, try fromField");
						var p = fromField(e,field);
						if (p == null) 
							out(error());
						p;

					case _:
						trace("Inlined Expression cannot be resolved");
						
						trace("Trigger inline error for sublime, the inline workaround can be triggered from there.");
						out(error("inlined"));
						None;
						
						
				}
			case ECall({expr : EField(e,field)}, args) if (args.length == 0):
				trace("Expression is an ECall from an EField, try fromField");
				var p = fromField(e,field);
				if (p == null) 
					out(error());
				p;

			case _:
				out(error());
				None;
		}
	}


	static function checkByType(e) {
		var te = try {
			var typeStr = haxe.macro.ExprTools.toString(e);
			trace("try getType");
			Some(Context.getType(typeStr));

		} catch (_:Dynamic) {
			try {
				trace("try typeof");
				Some(Context.typeof(e));
			} catch (_:Dynamic) {
				trace("catched");
				// cannot type expression, it could be a typedef
				try {

					trace("here");
					var typeStr = haxe.macro.ExprTools.toString(e);
					trace(typeStr);
					var test = '{ var x : $typeStr = null; x;}';
					trace(test);
					Some(Context.typeof(Context.parse(test, Context.currentPos())));

				} catch (_:Dynamic) {
					None;
				}
			}
			
		}
		trace(te);
		return switch (te) 
		{
			case Some(te = TType(t, params)):
				trace("Expr is a TType");
				mkFieldInfos(t.get(),te);
			case Some(te = TInst(t, params)):
				
				mkFieldInfos(t.get(),te);
			case Some(te = TAbstract(t, params)):
				
				mkFieldInfos(t.get(),te);

			case Some(te = TEnum(t, params)):
				mkFieldInfos(t.get(),te);	

			case Some(te = TFun(args, ret)):
				checkRegular(e);
				//mkFieldInfos(t.get(),te);
			
			
			case t:
				trace("NONE FOR TYPE: " + t);
				None;
		
		}
	}

	static function sublimeFindDecl (e:Expr, formatField:FieldInfosWithTypeData->String, id:Int) 
	{
		redirectTrace();

		trace("-------------------");
		trace("Find Declaration of Expr: " + e.toString());


		var order = id == 1 ? [checkRegular, checkByType] : [checkByType, checkRegular];

		var info = None;

		for (o in order) {
			info = o(e);
			if (info != None) break;
		}

		


		if (info != None) {
			outResult(info, formatField);
		}
		out("-------------------");
		return macro null;
	}


	#end



	macro public static function __sublimeFindDecl (e:ExprOf<Dynamic>, id:Int):Expr 
	{
		return sublimeFindDecl(e, function (f) return formatPos(f.field.pos), id);
	}
	macro public static function __sublimeShowDoc (e:ExprOf<Dynamic>, id:Int):Expr 
	{
		return sublimeFindDecl(e, function (f) return formatDoc(f), id);
	}

}